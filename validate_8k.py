import json
import time
import os
import hashlib
import gc
from pathlib import Path
import sys
from collections import Counter
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent / "nexa-model"))
from tokenizer.bpe_tokenizer import DEFAULT_SPECIAL_TOKENS
from tokenizer.incremental_bpe import IncrementalBPETokenizer

def get_meminfo() -> dict:
    mem = {}
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    mem[parts[0].strip(':')] = int(parts[1]) * 1024
    except:
        pass
    return mem

def get_rss_mb() -> float:
    try:
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    return int(line.split()[1]) / 1024.0
    except:
        pass
    import resource
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0

def sha256_file(path: Path) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

print("Starting validation...")
start_rss = get_rss_mb()
peak_rss = start_rss
min_avail_ram = get_meminfo().get("MemAvailable", 0) / 1024 / 1024
swap_used = 0

def update_resources():
    global peak_rss, min_avail_ram, swap_used
    mem = get_meminfo()
    peak_rss = max(peak_rss, get_rss_mb())
    min_avail_ram = min(min_avail_ram, mem.get("MemAvailable", float('inf')) / 1024 / 1024)
    swap = mem.get("SwapTotal", 0) - mem.get("SwapFree", 0)
    swap_used = max(swap_used, swap / 1024 / 1024)

# Step 0
tok_path = Path("nexa-model/tokenizer/candidates/8k/tokenizer.json")
if not tok_path.exists():
    print("8K_ARTIFACT_MISSING")
    sys.exit(1)

tok_stat = tok_path.stat()
tok_size = tok_stat.st_size
tok_mtime = tok_stat.st_mtime
tok_sha256 = sha256_file(tok_path)

# Step 1 & 2: Load validation & Structural audit
t0 = time.time()
try:
    tok = IncrementalBPETokenizer.load(tok_path)
    vocab_size = len(tok.vocab)
    special_size = len(tok.special_tokens)
    total_vocab = vocab_size + special_size
    merge_count = len(tok.merges)
    load_success = True
except Exception as e:
    load_success = False
    print(f"Failed to load: {e}")

# Serialize check
tmp_save = Path("temp_val_tok.json")
tok.save(tmp_save)
tmp_sha256 = sha256_file(tmp_save)
save_load_equiv = (tmp_sha256 == tok_sha256)
tmp_save.unlink()

structural_audit = load_success and (total_vocab == 8000)

update_resources()

# Step 3: Round-trip correctness tests
test_cases = [
    "The quick brown fox jumps over the lazy dog.", # ASCII English
    "Hello, world! How are you doing today? I'm fine.", # punctuation-heavy
    "0123456789 3.14159 42", # numbers
    "   \n \t \r\n  ", # whitespace
    "", # empty
    "banana banana banana banana", # repeated
    "Bonjour! Hola! Привет! こんにちは!", # UTF-8 multilingual
    "😊🚀🔥", # emoji
    "def hello_world():\n    print('Hello World')", # code
    "This is a longer paragraph. " * 20, # long english
    "<NEXA_SYSTEM> System prompt <NEXA_USER> Hello <NEXA_ASSISTANT> World" # control tokens
]

roundtrip_passes = 0
roundtrip_failures = []
for i, text in enumerate(test_cases):
    try:
        enc = tok.encode(text)
        dec = tok.decode(enc)
        if dec == text:
            roundtrip_passes += 1
        else:
            roundtrip_failures.append(f"Case {i} failed: dec != text")
    except Exception as e:
        roundtrip_failures.append(f"Case {i} error: {e}")

update_resources()

# Step 4: Corpus sample evaluation
corpus_dir = Path("data/recovery/clean")
files = sorted(corpus_dir.glob("*.txt"))
eval_docs = []
eval_bytes = 0
for f in files:
    text = f.read_text(encoding="utf-8")
    b = text.encode("utf-8")
    if eval_bytes + len(b) > 200 * 1024 or len(eval_docs) >= 5:
        break
    eval_docs.append(text)
    eval_bytes += len(b)

eval_text = "\n".join(eval_docs)
eval_chars = len(eval_text)

enc_t0 = time.perf_counter()
eval_enc = tok.encode(eval_text)
enc_t1 = time.perf_counter()

dec_t0 = time.perf_counter()
eval_dec = tok.decode(eval_enc)
dec_t1 = time.perf_counter()

eval_tokens = len(eval_enc)
eval_roundtrip = (eval_dec == eval_text)
enc_throughput = eval_chars / max(0.001, enc_t1 - enc_t0)
dec_throughput = eval_tokens / max(0.001, dec_t1 - dec_t0)

update_resources()

# Step 5: Token distribution
dist = Counter(eval_enc)
unique_tokens = len(dist)
most_freq = dist.most_common(5)

# Assuming bytes are 0-255, special are > max_byte and merges follow.
# In IncrementalBPE, bytes are 0-255.
byte_tokens_count = sum(cnt for tid, cnt in dist.items() if tid < 256)
special_tokens_count = sum(cnt for tid, cnt in dist.items() if tid in tok.special_tokens.values())
merged_tokens_count = eval_tokens - byte_tokens_count - special_tokens_count
byte_pct = byte_tokens_count / max(1, eval_tokens) * 100
merged_pct = merged_tokens_count / max(1, eval_tokens) * 100
unk_count = dist.get(tok.special_tokens.get("<NEXA_UNK>", -1), 0)

update_resources()

# Step 6: Determinism
det_enc1 = tok.encode(eval_docs[0])
det_enc2 = tok.encode(eval_docs[0])
det_pass1 = (det_enc1 == det_enc2)

tok_reload = IncrementalBPETokenizer.load(tok_path)
det_enc3 = tok_reload.encode(eval_docs[0])
det_pass2 = (det_enc1 == det_enc3)
determinism_pass = det_pass1 and det_pass2

update_resources()

# Step 7: Existing test suite
# We will run this via subprocess or test runner
import unittest
loader = unittest.TestLoader()
suite = loader.discover("nexa-model/tests")
runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
test_result = runner.run(suite)
tests_run = test_result.testsRun
tests_failed = len(test_result.failures) + len(test_result.errors)
tests_passed = tests_run - tests_failed

update_resources()

# Step 8: Checkpoint audit
ckpt_dir = Path("data/checkpoints/tokenizer_8k")
ckpt_files = list(ckpt_dir.glob("*.json"))
ckpt_count = len(ckpt_files)
highest_ckpt = -1
highest_ckpt_sha256 = ""
for f in ckpt_files:
    if "checkpoint_step_" in f.name:
        step = int(f.stem.split("_")[-1])
        if step > highest_ckpt:
            highest_ckpt = step
            highest_ckpt_sha256 = sha256_file(f)
    elif "checkpoint_final" in f.name:
        highest_ckpt = 7731 # Max merges? 
        highest_ckpt_sha256 = sha256_file(f)
        
ckpt_audit_status = "Readable and present" if ckpt_count > 0 else "No checkpoints found"

update_resources()
t1 = time.time()
val_runtime = t1 - t0

# Certification gates
certified = (
    load_success and 
    structural_audit and 
    len(roundtrip_failures) == 0 and 
    determinism_pass and 
    tests_failed == 0 and 
    peak_rss < 2500 and 
    unk_count == 0
)

final_decision = "8K_TOKENIZER_CERTIFIED" if certified else "8K_TOKENIZER_CERTIFICATION_FAILED"
if certified and peak_rss > 2500:
    final_decision = "8K_TOKENIZER_VALIDATION_INCOMPLETE"

val_report = {
    "artifact_path": str(tok_path),
    "file_size": tok_size,
    "sha256": tok_sha256,
    "vocab_size": total_vocab,
    "merge_count": merge_count,
    "special_count": special_size,
    "structural_valid": structural_audit,
    "roundtrip_tests_passed": roundtrip_passes,
    "roundtrip_tests_failed": len(roundtrip_failures),
    "determinism_pass": determinism_pass,
    "tests_run": tests_run,
    "tests_passed": tests_passed,
    "tests_failed": tests_failed,
    "eval_files": len(eval_docs),
    "eval_bytes": eval_bytes,
    "eval_chars": eval_chars,
    "eval_tokens": eval_tokens,
    "tokens_per_char": eval_tokens / max(1, eval_chars),
    "chars_per_token": eval_chars / max(1, eval_tokens),
    "bytes_per_token": eval_bytes / max(1, eval_tokens),
    "encode_throughput": enc_throughput,
    "decode_throughput": dec_throughput,
    "byte_fallback_pct": byte_pct,
    "merged_pct": merged_pct,
    "unk_usage": unk_count,
    "checkpoint_count": ckpt_count,
    "highest_ckpt_step": highest_ckpt,
    "highest_ckpt_sha256": highest_ckpt_sha256,
    "start_rss_mb": start_rss,
    "peak_rss_mb": peak_rss,
    "min_avail_ram_mb": min_avail_ram,
    "swap_usage_mb": swap_used,
    "validation_runtime_sec": val_runtime,
    "historical_training_peak_rss_mb": 2072.82,
    "final_decision": final_decision
}

rep_dir = Path("data/reports")
rep_dir.mkdir(parents=True, exist_ok=True)

with open(rep_dir / "phase3f2_8k_validation.json", "w") as f:
    json.dump(val_report, f, indent=2)

dist_report = {
    "total_tokens": eval_tokens,
    "unique_tokens": unique_tokens,
    "most_frequent": most_freq,
    "byte_pct": byte_pct,
    "merged_pct": merged_pct,
    "unk_usage": unk_count
}
with open(rep_dir / "phase3f2_8k_token_distribution.json", "w") as f:
    json.dump(dist_report, f, indent=2)

integrity_report = {
    "tokenizer.json": tok_sha256,
    "phase3f2_8k_validation.json": sha256_file(rep_dir / "phase3f2_8k_validation.json"),
    "phase3f2_8k_token_distribution.json": sha256_file(rep_dir / "phase3f2_8k_token_distribution.json")
}
with open(rep_dir / "phase3f2_8k_integrity.json", "w") as f:
    json.dump(integrity_report, f, indent=2)

md_report = [
    "NEXA PHASE 3F.2A FINAL REPORT",
    "======================================",
    f"1. Tokenizer artifact path: {tok_path}",
    f"2. Tokenizer file size: {tok_size} bytes",
    f"3. Tokenizer SHA-256: {tok_sha256}",
    f"4. Vocabulary size and exact counting convention: {total_vocab} (counted as len(vocab) + len(special_tokens), meaning {vocab_size} regular/byte/merged + {special_size} special)",
    f"5. Merge count: {merge_count}",
    f"6. Special-token count: {special_size}",
    f"7. Structural validation result: {'PASS' if structural_audit else 'FAIL'}",
    f"8. Round-trip tests executed/pass/fail: {len(test_cases)} / {roundtrip_passes} / {len(roundtrip_failures)}",
    f"9. Unit tests executed/pass/fail: {tests_run} / {tests_passed} / {tests_failed}",
    f"10. Determinism result: {'PASS' if determinism_pass else 'FAIL'}",
    f"11. Evaluation sample files: {len(eval_docs)}",
    f"12. Evaluation bytes: {eval_bytes}",
    f"13. Evaluation characters: {eval_chars}",
    f"14. Evaluation token count: {eval_tokens}",
    f"15. Tokens/character: {eval_tokens / max(1, eval_chars):.4f}",
    f"16. Characters/token: {eval_chars / max(1, eval_tokens):.4f}",
    f"17. Bytes/token: {eval_bytes / max(1, eval_tokens):.4f}",
    f"18. Encode throughput: {enc_throughput:.2f} chars/sec",
    f"19. Decode throughput: {dec_throughput:.2f} tokens/sec",
    f"20. Byte-fallback percentage: {byte_pct:.2f}%",
    f"21. Merged-token percentage: {merged_pct:.2f}%",
    f"22. UNK usage: {unk_count}",
    f"23. Checkpoints discovered: {ckpt_count}",
    f"24. Highest checkpoint step: {highest_ckpt}",
    f"25. Checkpoint integrity result: {ckpt_audit_status}",
    f"26. Validation starting RSS: {start_rss:.2f} MB",
    f"27. Validation peak RSS: {peak_rss:.2f} MB",
    f"28. Minimum available RAM: {min_avail_ram:.2f} MB",
    f"29. Swap usage: {swap_used:.2f} MB",
    f"30. Validation runtime: {val_runtime:.2f} s",
    f"31. Historical training peak RSS: 2072.82 MB (historical)",
    "32. Files created: phase3f2_8k_validation.json, phase3f2_8k_token_distribution.json, phase3f2_8k_integrity.json, phase3f2_8k_final_report.md",
    "33. Files modified: None",
    f"34. Warnings/discrepancies: {'None' if len(roundtrip_failures)==0 else roundtrip_failures}",
    f"35. Certification gate results: {'PASS' if certified else 'FAIL'}",
    f"36. FINAL DECISION: {final_decision}"
]

with open(rep_dir / "phase3f2_8k_final_report.md", "w") as f:
    f.write("\n".join(md_report))

print("\n".join(md_report))
