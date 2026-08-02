<<<<<<< HEAD
import argparse
import json
import os
import sys
import hashlib
import time
from datetime import datetime
from pathlib import Path
from collections import defaultdict, Counter
from typing import Iterable, List, Union
import statistics
import tempfile
import gc

sys.path.insert(0, str(Path(r"C:\Users\amogh\OneDrive\c++\project 2") / "nexa-model"))

from tokenizer.bpe_tokenizer import NexaBPETokenizer
from data.pipeline import ingest_directory, process_documents
try:
    import psutil
except Exception:
    psutil = None

repo = Path(r"C:\Users\amogh\OneDrive\c++\project 2")
clean_dir = repo / "nexa-model" / "data" / "clean" / "pd5m_v6"
output_base = repo / "tokenizers" / "experiments"
telemetry_path = repo / "data" / "reports" / "phase3f_resource_usage.jsonl"

# Load special tokens with NEXA control tokens
SPECIAL_TOKENS = {
    "<PAD>": 0,
    "<BOS>": 1,
    "<EOS>": 2,
    "<UNK>": 3,
    "<NEXA_PAD>": 4,
    "<NEXA_BOS>": 5,
    "<NEXA_EOS>": 6,
    "<NEXA_UNK>": 7,
    "<NEXA_SYSTEM>": 8,
    "<NEXA_USER>": 9,
    "<NEXA_ASSISTANT>": 10,
    "<NEXA_END>": 11,
}

MIN_RAM_BYTES = 1.5 * 1024 * 1024 * 1024
PRESTART_RAM_BYTES = 4 * 1024 * 1024 * 1024
WARN_RAM_BYTES = 2 * 1024 * 1024 * 1024

# Internal testing helpers: allow a one-shot sequence of fake available-RAM values
_fake_sequence = None
_fake_seq_idx = 0

def get_system_metrics() -> dict:
    if psutil is None:
        raise RuntimeError("psutil is required for resource telemetry and safety checks")

    # Test hook: allow overriding available RAM and cpu via environment variables
    global _fake_sequence, _fake_seq_idx

    fake_avail = os.environ.get("PHASE3F_FAKE_AVAILABLE_RAM")
    fake_cpu = os.environ.get("PHASE3F_FAKE_CPU")
    fake_seq = os.environ.get("PHASE3F_FAKE_SEQUENCE")

    # Initialize sequence once if provided
    if _fake_sequence is None and fake_seq:
        try:
            _fake_sequence = [int(x) for x in fake_seq.split(",") if x.strip()]
            _fake_seq_idx = 0
        except Exception:
            _fake_sequence = None

    vm = psutil.virtual_memory()
    proc = psutil.Process()
    cpu = psutil.cpu_percent(interval=0.1)

    # If a sequence is present, consume next value on each call
    if _fake_sequence:
        if _fake_seq_idx < len(_fake_sequence):
            vm_available = _fake_sequence[_fake_seq_idx]
            _fake_seq_idx += 1
        else:
            vm_available = _fake_sequence[-1]
    elif fake_avail is not None:
        try:
            vm_available = int(fake_avail)
        except Exception:
            vm_available = vm.available
    else:
        vm_available = vm.available

    if fake_cpu is not None:
        try:
            cpu = float(fake_cpu)
        except Exception:
            pass

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "process_rss": proc.memory_info().rss,
        "system_available_ram": vm_available,
        "system_ram_percent": vm.percent,
        "cpu_percent": cpu,
    }


def write_telemetry(entry: dict) -> None:
    os.makedirs(telemetry_path.parent, exist_ok=True)
    with open(telemetry_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def assert_writable_path(path: Path) -> None:
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "a", encoding="utf-8"):
        pass


def load_corpus_manifest() -> List[Path]:
    manifest_file = repo / "data" / "acquisition" / "pd5m_v6" / "final_corpus_manifest.json"
    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    doc_paths = []
    for entry in manifest:
        sid = entry["source_id"]
        cp = clean_dir / f"{sid}.txt"
        if cp.exists():
            doc_paths.append(cp)
    return doc_paths


def healthy_ram(required_bytes: float) -> bool:
    metrics = get_system_metrics()
    return metrics["system_available_ram"] >= required_bytes


def phase_print_header():
    print("=" * 60)
    print("PHASE 3F.1 — TOKENIZER BENCHMARK")
    print("=" * 60)


phase_print_header()

print("\nPreparing dry-run safety environment...")
if psutil is None:
    raise RuntimeError("psutil is required for phase 3F.1 safety telemetry")

try:
    assert_writable_path(telemetry_path)
except Exception as exc:
    raise RuntimeError(f"Telemetry path not writable: {telemetry_path}") from exc

manifest_paths = load_corpus_manifest()
print(f"Found {len(manifest_paths)} manifest entries")

def preflight_check() -> None:
    metrics = get_system_metrics()
    entry = {
        "phase": "preflight",
        "candidate_vocab": "none",
        "message": "preflight check",
        "elapsed_time": 0.0,
        **metrics,
    }
    write_telemetry(entry)

    if metrics["system_available_ram"] < PRESTART_RAM_BYTES:
        raise RuntimeError(
            f"Pre-start RAM gate failed: available {metrics['system_available_ram'] / (1024 ** 3):.2f} GB < 4.00 GB"
        )
    if metrics["system_available_ram"] < WARN_RAM_BYTES:
        print(f"WARNING: available RAM below 2GB: {metrics['system_available_ram'] / (1024 ** 3):.2f} GB")


def record_phase(candidate_vocab: str, phase: str, start_time: float, message: str = "") -> None:
    metrics = get_system_metrics()
    entry = {
        "phase": phase,
        "candidate_vocab": candidate_vocab,
        "message": message,
        "elapsed_time": time.time() - start_time,
        **metrics,
    }
    write_telemetry(entry)


def safe_abort(candidate_vocab: str, phase: str, reason: str, start_time: float) -> None:
    record_phase(candidate_vocab, phase, start_time, message=f"ABORT: {reason}")
    raise RuntimeError(reason)


def safe_train_candidate(vocab_size: int, doc_paths: List[Path]) -> NexaBPETokenizer:
    name = f"nexa_bpe_{vocab_size // 1000}k"
    out_dir = output_base / name
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n--- Preparing {name} (vocab={vocab_size}) ---")
    candidate_start = time.time()
    metrics = get_system_metrics()
    if metrics["system_available_ram"] < PRESTART_RAM_BYTES:
        safe_abort(name, "preflight", f"insufficient RAM before candidate: {metrics['system_available_ram']}", candidate_start)
    if metrics["system_available_ram"] < WARN_RAM_BYTES:
        print(f"WARNING: available RAM below 2GB before {name}: {metrics['system_available_ram'] / (1024 ** 3):.2f} GB")

    record_phase(name, "preflight", candidate_start, message="candidate start")

    # Dry-run mode: do not perform actual training, test the call path only
    print(f"Dry-run: initializing tokenizer for {name}")
    tok = NexaBPETokenizer(vocab_size=vocab_size, min_frequency=2, special_tokens=SPECIAL_TOKENS)

    # verify output directory is writable
    assert_writable_path(out_dir / "dummy.check")

    # Optionally simulate a training loop for safety checks when requested.
    # Set environment variable PHASE3F_SIMULATE_TRAINING=1 to run the simulation
    simulate = os.environ.get("PHASE3F_SIMULATE_TRAINING") == "1"
    if simulate:
        print(f"Simulating training loop for {name} (no merges performed) to validate resource gates")
        merges_to_simulate = min(64, max(8, vocab_size // 256))
        for merge_idx in range(merges_to_simulate):
            metrics = get_system_metrics()
            # Hard abort if below MIN_RAM_BYTES
            if metrics["system_available_ram"] < MIN_RAM_BYTES:
                safe_abort(name, "training", f"available RAM below hard abort threshold: {metrics['system_available_ram']}", candidate_start)
            # Warn if below WARN_RAM_BYTES
            if metrics["system_available_ram"] < WARN_RAM_BYTES:
                print(f"WARNING: low memory during streaming at merge {merge_idx}: available {metrics['system_available_ram'] / (1024 ** 3):.2f} GB")
            # Periodically record telemetry
            if merge_idx % 8 == 0:
                record_phase(name, "training", candidate_start, message=f"simulated merge {merge_idx}")
            # small sleep to let cpu_percent measurements stabilize when running locally
            time.sleep(0.01)

    else:
        # do not start actual merge training in dry-run
        record_phase(name, "training", candidate_start, message="dry-run no training")

    record_phase(name, "cleanup", candidate_start, message="dry-run cleanup")

    return tok


preflight_check()

# Train candidates dry-run
candidates = {}
for vocab_size in [8000, 12000, 16000]:
    tok = safe_train_candidate(vocab_size, manifest_paths)
    candidates[f"nexa_bpe_{vocab_size // 1000}k"] = tok
    tok = None
    gc.collect()
    metrics = get_system_metrics()
    record_phase(f"nexa_bpe_{vocab_size // 1000}k", "post_cleanup", time.time(), message="candidate released")
    print(f"  Post-cleanup available RAM: {metrics['system_available_ram'] / (1024**3):.2f} GB")

# Benchmark on deterministic eval sample (20 docs from corpus)
eval_size = min(20, len(manifest_paths))
eval_texts = []
for p in manifest_paths[:eval_size]:
    try:
        eval_texts.append(p.read_text(encoding='utf-8', errors='replace'))
    except Exception:
        eval_texts.append("")
eval_full = "\n\n".join(eval_texts)
eval_bytes = len(eval_full.encode('utf-8'))

print(f"\n{'=' * 60}")
print("BENCHMARK RESULTS")
print(f"{'=' * 60}")
print(f"Evaluation sample: {eval_size} docs, {len(eval_full):,} chars, {eval_bytes:,} bytes")

results = {}
for name, tok in candidates.items():
    tokens = tok.encode(eval_full)
    decoded = tok.decode(tokens)
    
    # Metrics
    total_tokens = len(tokens)
    chars_per_token = len(eval_full) / total_tokens
    bytes_per_token = eval_bytes / total_tokens
    words = len(eval_full.split())
    tokens_per_word = total_tokens / words if words > 0 else 0
    compression = eval_bytes / (total_tokens * 2)  # rough: avg 2 bytes per token in model
    
    # Token length stats
    token_lengths = [len(tok.vocab.get(t, b'')) for t in tokens if t not in SPECIAL_TOKENS.values()]
    if token_lengths:
        p50 = statistics.median(token_lengths)
        p90 = sorted(token_lengths)[int(len(token_lengths) * 0.9)]
        p95 = sorted(token_lengths)[int(len(token_lengths) * 0.95)]
        p99 = sorted(token_lengths)[int(len(token_lengths) * 0.99)]
    else:
        p50 = p90 = p95 = p99 = 0
    
    # Round-trip preservation
    rt_match = decoded == eval_full
    
    # Count special token collisions in normal text
    collision_count = sum(eval_full.count(st) for st in SPECIAL_TOKENS if st != "<PAD>")
    
    results[name] = {
        "vocab_size": len(tok.vocab),
        "total_tokens": total_tokens,
        "chars_per_token": round(chars_per_token, 2),
        "bytes_per_token": round(bytes_per_token, 2),
        "tokens_per_word": round(tokens_per_word, 2),
        "compression_ratio": round(compression, 3),
        "p50_token_len": p50,
        "p90_token_len": p90,
        "p95_token_len": p95,
        "p99_token_len": p99,
        "round_trip_exact": rt_match,
        "special_collisions": collision_count,
    }
    
    print(f"\n{name}:")
    for k, v in results[name].items():
        print(f"  {k}: {v}")

# Model parameter calculations
print(f"\n{'=' * 60}")
print("MODEL PARAMETER IMPACT")
print(f"{'=' * 60}")
layers = 6
heads = 6
d_model = 384
context = 512

for name, r in results.items():
    V = r['vocab_size']
    emb_params = V * d_model
    output_params = V * d_model  # tied or untied same size
    total = layers * (4 * d_model * d_model + 2 * d_model) + emb_params + output_params
    fp32_mb = total * 4 / (1024 * 1024)
    fp16_mb = total * 2 / (1024 * 1024)
    print(f"\n{name} (V={V}):")
    print(f"  Embedding params: {emb_params:,}")
    print(f"  Output params: {output_params:,}")
    print(f"  Total params: {total:,}")
    print(f"  FP32 size: {fp32_mb:.1f} MB")
    print(f"  FP16 size: {fp16_mb:.1f} MB")

# Save benchmark
benchmark = {
    "corpus_version": "NEXA-PD5M-v6.1",
    "eval_sample_size": eval_size,
    "eval_chars": len(eval_full),
    "eval_bytes": eval_bytes,
    "candidates": results,
}
with open(output_base / "benchmark.json", "w") as f:
    json.dump(benchmark, f, indent=2)
=======
import argparse
import json
import os
import sys
import hashlib
import time
from datetime import datetime
from pathlib import Path
from collections import defaultdict, Counter
from typing import Iterable, List, Union
import statistics
import tempfile
import gc

sys.path.insert(0, str(Path(r"C:\Users\amogh\OneDrive\c++\project 2") / "nexa-model"))

from tokenizer.bpe_tokenizer import NexaBPETokenizer
from data.pipeline import ingest_directory, process_documents
try:
    import psutil
except Exception:
    psutil = None

repo = Path(r"C:\Users\amogh\OneDrive\c++\project 2")
clean_dir = repo / "nexa-model" / "data" / "clean" / "pd5m_v6"
output_base = repo / "tokenizers" / "experiments"
telemetry_path = repo / "data" / "reports" / "phase3f_resource_usage.jsonl"

# Load special tokens with NEXA control tokens
SPECIAL_TOKENS = {
    "<PAD>": 0,
    "<BOS>": 1,
    "<EOS>": 2,
    "<UNK>": 3,
    "<NEXA_PAD>": 4,
    "<NEXA_BOS>": 5,
    "<NEXA_EOS>": 6,
    "<NEXA_UNK>": 7,
    "<NEXA_SYSTEM>": 8,
    "<NEXA_USER>": 9,
    "<NEXA_ASSISTANT>": 10,
    "<NEXA_END>": 11,
}

MIN_RAM_BYTES = 1.5 * 1024 * 1024 * 1024
PRESTART_RAM_BYTES = 4 * 1024 * 1024 * 1024
WARN_RAM_BYTES = 2 * 1024 * 1024 * 1024

# Internal testing helpers: allow a one-shot sequence of fake available-RAM values
_fake_sequence = None
_fake_seq_idx = 0

def get_system_metrics() -> dict:
    if psutil is None:
        raise RuntimeError("psutil is required for resource telemetry and safety checks")

    # Test hook: allow overriding available RAM and cpu via environment variables
    global _fake_sequence, _fake_seq_idx

    fake_avail = os.environ.get("PHASE3F_FAKE_AVAILABLE_RAM")
    fake_cpu = os.environ.get("PHASE3F_FAKE_CPU")
    fake_seq = os.environ.get("PHASE3F_FAKE_SEQUENCE")

    # Initialize sequence once if provided
    if _fake_sequence is None and fake_seq:
        try:
            _fake_sequence = [int(x) for x in fake_seq.split(",") if x.strip()]
            _fake_seq_idx = 0
        except Exception:
            _fake_sequence = None

    vm = psutil.virtual_memory()
    proc = psutil.Process()
    cpu = psutil.cpu_percent(interval=0.1)

    # If a sequence is present, consume next value on each call
    if _fake_sequence:
        if _fake_seq_idx < len(_fake_sequence):
            vm_available = _fake_sequence[_fake_seq_idx]
            _fake_seq_idx += 1
        else:
            vm_available = _fake_sequence[-1]
    elif fake_avail is not None:
        try:
            vm_available = int(fake_avail)
        except Exception:
            vm_available = vm.available
    else:
        vm_available = vm.available

    if fake_cpu is not None:
        try:
            cpu = float(fake_cpu)
        except Exception:
            pass

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "process_rss": proc.memory_info().rss,
        "system_available_ram": vm_available,
        "system_ram_percent": vm.percent,
        "cpu_percent": cpu,
    }


def write_telemetry(entry: dict) -> None:
    os.makedirs(telemetry_path.parent, exist_ok=True)
    with open(telemetry_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def assert_writable_path(path: Path) -> None:
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "a", encoding="utf-8"):
        pass


def load_corpus_manifest() -> List[Path]:
    manifest_file = repo / "data" / "acquisition" / "pd5m_v6" / "final_corpus_manifest.json"
    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    doc_paths = []
    for entry in manifest:
        sid = entry["source_id"]
        cp = clean_dir / f"{sid}.txt"
        if cp.exists():
            doc_paths.append(cp)
    return doc_paths


def healthy_ram(required_bytes: float) -> bool:
    metrics = get_system_metrics()
    return metrics["system_available_ram"] >= required_bytes


def phase_print_header():
    print("=" * 60)
    print("PHASE 3F.1 — TOKENIZER BENCHMARK")
    print("=" * 60)


phase_print_header()

print("\nPreparing dry-run safety environment...")
if psutil is None:
    raise RuntimeError("psutil is required for phase 3F.1 safety telemetry")

try:
    assert_writable_path(telemetry_path)
except Exception as exc:
    raise RuntimeError(f"Telemetry path not writable: {telemetry_path}") from exc

manifest_paths = load_corpus_manifest()
print(f"Found {len(manifest_paths)} manifest entries")

def preflight_check() -> None:
    metrics = get_system_metrics()
    entry = {
        "phase": "preflight",
        "candidate_vocab": "none",
        "message": "preflight check",
        "elapsed_time": 0.0,
        **metrics,
    }
    write_telemetry(entry)

    if metrics["system_available_ram"] < PRESTART_RAM_BYTES:
        raise RuntimeError(
            f"Pre-start RAM gate failed: available {metrics['system_available_ram'] / (1024 ** 3):.2f} GB < 4.00 GB"
        )
    if metrics["system_available_ram"] < WARN_RAM_BYTES:
        print(f"WARNING: available RAM below 2GB: {metrics['system_available_ram'] / (1024 ** 3):.2f} GB")


def record_phase(candidate_vocab: str, phase: str, start_time: float, message: str = "") -> None:
    metrics = get_system_metrics()
    entry = {
        "phase": phase,
        "candidate_vocab": candidate_vocab,
        "message": message,
        "elapsed_time": time.time() - start_time,
        **metrics,
    }
    write_telemetry(entry)


def safe_abort(candidate_vocab: str, phase: str, reason: str, start_time: float) -> None:
    record_phase(candidate_vocab, phase, start_time, message=f"ABORT: {reason}")
    raise RuntimeError(reason)


def safe_train_candidate(vocab_size: int, doc_paths: List[Path]) -> NexaBPETokenizer:
    name = f"nexa_bpe_{vocab_size // 1000}k"
    out_dir = output_base / name
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n--- Preparing {name} (vocab={vocab_size}) ---")
    candidate_start = time.time()
    metrics = get_system_metrics()
    if metrics["system_available_ram"] < PRESTART_RAM_BYTES:
        safe_abort(name, "preflight", f"insufficient RAM before candidate: {metrics['system_available_ram']}", candidate_start)
    if metrics["system_available_ram"] < WARN_RAM_BYTES:
        print(f"WARNING: available RAM below 2GB before {name}: {metrics['system_available_ram'] / (1024 ** 3):.2f} GB")

    record_phase(name, "preflight", candidate_start, message="candidate start")

    # Dry-run mode: do not perform actual training, test the call path only
    print(f"Dry-run: initializing tokenizer for {name}")
    tok = NexaBPETokenizer(vocab_size=vocab_size, min_frequency=2, special_tokens=SPECIAL_TOKENS)

    # verify output directory is writable
    assert_writable_path(out_dir / "dummy.check")

    # Optionally simulate a training loop for safety checks when requested.
    # Set environment variable PHASE3F_SIMULATE_TRAINING=1 to run the simulation
    simulate = os.environ.get("PHASE3F_SIMULATE_TRAINING") == "1"
    if simulate:
        print(f"Simulating training loop for {name} (no merges performed) to validate resource gates")
        merges_to_simulate = min(64, max(8, vocab_size // 256))
        for merge_idx in range(merges_to_simulate):
            metrics = get_system_metrics()
            # Hard abort if below MIN_RAM_BYTES
            if metrics["system_available_ram"] < MIN_RAM_BYTES:
                safe_abort(name, "training", f"available RAM below hard abort threshold: {metrics['system_available_ram']}", candidate_start)
            # Warn if below WARN_RAM_BYTES
            if metrics["system_available_ram"] < WARN_RAM_BYTES:
                print(f"WARNING: low memory during streaming at merge {merge_idx}: available {metrics['system_available_ram'] / (1024 ** 3):.2f} GB")
            # Periodically record telemetry
            if merge_idx % 8 == 0:
                record_phase(name, "training", candidate_start, message=f"simulated merge {merge_idx}")
            # small sleep to let cpu_percent measurements stabilize when running locally
            time.sleep(0.01)

    else:
        # do not start actual merge training in dry-run
        record_phase(name, "training", candidate_start, message="dry-run no training")

    record_phase(name, "cleanup", candidate_start, message="dry-run cleanup")

    return tok


preflight_check()

# Train candidates dry-run
candidates = {}
for vocab_size in [8000, 12000, 16000]:
    tok = safe_train_candidate(vocab_size, manifest_paths)
    candidates[f"nexa_bpe_{vocab_size // 1000}k"] = tok
    tok = None
    gc.collect()
    metrics = get_system_metrics()
    record_phase(f"nexa_bpe_{vocab_size // 1000}k", "post_cleanup", time.time(), message="candidate released")
    print(f"  Post-cleanup available RAM: {metrics['system_available_ram'] / (1024**3):.2f} GB")

# Benchmark on deterministic eval sample (20 docs from corpus)
eval_size = min(20, len(manifest_paths))
eval_texts = []
for p in manifest_paths[:eval_size]:
    try:
        eval_texts.append(p.read_text(encoding='utf-8', errors='replace'))
    except Exception:
        eval_texts.append("")
eval_full = "\n\n".join(eval_texts)
eval_bytes = len(eval_full.encode('utf-8'))

print(f"\n{'=' * 60}")
print("BENCHMARK RESULTS")
print(f"{'=' * 60}")
print(f"Evaluation sample: {eval_size} docs, {len(eval_full):,} chars, {eval_bytes:,} bytes")

results = {}
for name, tok in candidates.items():
    tokens = tok.encode(eval_full)
    decoded = tok.decode(tokens)
    
    # Metrics
    total_tokens = len(tokens)
    chars_per_token = len(eval_full) / total_tokens
    bytes_per_token = eval_bytes / total_tokens
    words = len(eval_full.split())
    tokens_per_word = total_tokens / words if words > 0 else 0
    compression = eval_bytes / (total_tokens * 2)  # rough: avg 2 bytes per token in model
    
    # Token length stats
    token_lengths = [len(tok.vocab.get(t, b'')) for t in tokens if t not in SPECIAL_TOKENS.values()]
    if token_lengths:
        p50 = statistics.median(token_lengths)
        p90 = sorted(token_lengths)[int(len(token_lengths) * 0.9)]
        p95 = sorted(token_lengths)[int(len(token_lengths) * 0.95)]
        p99 = sorted(token_lengths)[int(len(token_lengths) * 0.99)]
    else:
        p50 = p90 = p95 = p99 = 0
    
    # Round-trip preservation
    rt_match = decoded == eval_full
    
    # Count special token collisions in normal text
    collision_count = sum(eval_full.count(st) for st in SPECIAL_TOKENS if st != "<PAD>")
    
    results[name] = {
        "vocab_size": len(tok.vocab),
        "total_tokens": total_tokens,
        "chars_per_token": round(chars_per_token, 2),
        "bytes_per_token": round(bytes_per_token, 2),
        "tokens_per_word": round(tokens_per_word, 2),
        "compression_ratio": round(compression, 3),
        "p50_token_len": p50,
        "p90_token_len": p90,
        "p95_token_len": p95,
        "p99_token_len": p99,
        "round_trip_exact": rt_match,
        "special_collisions": collision_count,
    }
    
    print(f"\n{name}:")
    for k, v in results[name].items():
        print(f"  {k}: {v}")

# Model parameter calculations
print(f"\n{'=' * 60}")
print("MODEL PARAMETER IMPACT")
print(f"{'=' * 60}")
layers = 6
heads = 6
d_model = 384
context = 512

for name, r in results.items():
    V = r['vocab_size']
    emb_params = V * d_model
    output_params = V * d_model  # tied or untied same size
    total = layers * (4 * d_model * d_model + 2 * d_model) + emb_params + output_params
    fp32_mb = total * 4 / (1024 * 1024)
    fp16_mb = total * 2 / (1024 * 1024)
    print(f"\n{name} (V={V}):")
    print(f"  Embedding params: {emb_params:,}")
    print(f"  Output params: {output_params:,}")
    print(f"  Total params: {total:,}")
    print(f"  FP32 size: {fp32_mb:.1f} MB")
    print(f"  FP16 size: {fp16_mb:.1f} MB")

# Save benchmark
benchmark = {
    "corpus_version": "NEXA-PD5M-v6.1",
    "eval_sample_size": eval_size,
    "eval_chars": len(eval_full),
    "eval_bytes": eval_bytes,
    "candidates": results,
}
with open(output_base / "benchmark.json", "w") as f:
    json.dump(benchmark, f, indent=2)
>>>>>>> origin/main
print(f"\nBenchmark saved: {output_base / 'benchmark.json'}")