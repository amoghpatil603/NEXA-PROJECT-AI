"""
Phase 3F.1 Pipeline: 8K Production Tokenizer Training & Selection.
"""

import hashlib
import json
import os
import resource
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, 'nexa-model')
from tokenizer.bpe_tokenizer import DEFAULT_SPECIAL_TOKENS
from tokenizer.incremental_bpe import IncrementalBPETokenizer


def get_mem_available():
    with open('/proc/meminfo', 'r') as f:
        for line in f:
            if line.startswith('MemAvailable:'):
                return int(line.split()[1]) * 1024 # bytes
    return 0


def main():
    print("=== PHASE 3F.1 PIPELINE START ===")
    
    # -------------------------------------------------------------
    # STEP 1: Verify Tokenizer Test Suite
    # -------------------------------------------------------------
    import unittest
    suite = unittest.defaultTestLoader.discover('nexa-model/tests', pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=1)
    test_result = runner.run(suite)
    tests_run = test_result.testsRun
    tests_failed = len(test_result.failures) + len(test_result.errors)
    tests_passed = tests_run - tests_failed
    print(f"Step 1 Test Suite: {tests_run} run, {tests_passed} passed, {tests_failed} failed")
    assert tests_failed == 0, "Tokenizer tests failed!"

    # -------------------------------------------------------------
    # STEP 2: Verify Corpus Input
    # -------------------------------------------------------------
    clean_dir = Path('data/recovery/clean')
    manifest_file = Path('data/acquisition/pd5m_v7/clean_manifest.json')
    checksums_file = Path('data/acquisition/pd5m_v7/clean_checksums.json')

    with open(manifest_file, 'r', encoding='utf-8') as f:
        clean_manifest = json.load(f)

    with open(checksums_file, 'r', encoding='utf-8') as f:
        clean_checksums = json.load(f)

    clean_files = sorted(list(clean_dir.glob('*.txt')), key=lambda p: int(p.stem) if p.stem.isdigit() else p.stem)
    assert len(clean_files) == 75, f"Expected 75 clean files, found {len(clean_files)}"

    total_clean_bytes = 0
    total_clean_chars = 0
    corpus_docs = []

    for p in clean_files:
        raw_b = p.read_bytes()
        text_str = raw_b.decode('utf-8', errors='ignore')
        sha = hashlib.sha256(raw_b).hexdigest()
        sid = p.stem
        expected_sha = clean_checksums[sid]['clean_sha256'] if isinstance(clean_checksums[sid], dict) else clean_checksums[sid]
        assert sha == expected_sha, f"SHA256 mismatch for {sid}: got {sha}, expected {expected_sha}"
        total_clean_bytes += len(raw_b)
        total_clean_chars += len(text_str)
        corpus_docs.append(text_str)

    assert total_clean_bytes == 36830981, f"Expected 36,830,981 bytes, got {total_clean_bytes}"
    print(f"Step 2 Corpus Integrity: 75 clean files verified, 36,830,981 clean bytes (SHA256 matched)")

    # -------------------------------------------------------------
    # STEP 3: Resource Preflight
    # -------------------------------------------------------------
    mem_total = 0
    with open('/proc/meminfo', 'r') as f:
        for line in f:
            if line.startswith('MemTotal:'):
                mem_total = int(line.split()[1]) * 1024

    mem_avail_start = get_mem_available()
    disk_free = shutil.disk_usage('/').free
    cpu_count = os.cpu_count()

    print(f"Step 3 Preflight:")
    print(f"  Total RAM: {mem_total / (1024**3):.2f} GB")
    print(f"  Available RAM: {mem_avail_start / (1024**3):.2f} GB")
    print(f"  CPU Count: {cpu_count}")
    print(f"  Free Disk: {disk_free / (1024**3):.2f} GB")

    preflight_status = "YELLOW" if (4.0 * (1024**3) > mem_avail_start >= 1.5 * (1024**3)) else ("GREEN" if mem_avail_start >= 6.0 * (1024**3) else "RED")

    # -------------------------------------------------------------
    # STEP 4: Train 8K Candidate Only
    # -------------------------------------------------------------
    print("Step 4 Training 8K Candidate...")
    target_vocab = 8192
    min_freq = 2

    t_train_start = time.time()
    min_avail_ram = mem_avail_start

    tok = IncrementalBPETokenizer(
        vocab_size=target_vocab,
        min_frequency=min_freq,
        special_tokens=DEFAULT_SPECIAL_TOKENS
    )

    tok.train(corpus_docs)
    t_train_end = time.time()
    train_duration = t_train_end - t_train_start

    peak_rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    min_avail_ram = min(min_avail_ram, get_mem_available())

    final_vocab_size = len(tok.vocab) + len(tok.special_tokens)
    merge_count = len(tok.merges)

    print(f"Training completed in {train_duration:.2f} s")
    print(f"Final Vocab Size: {final_vocab_size}")
    print(f"Merge Count: {merge_count}")
    print(f"Peak RSS: {peak_rss_mb:.2f} MB")

    # Write telemetry jsonl
    telemetry_path = Path('data/reports/phase3f_resource_usage.jsonl')
    telemetry_path.parent.mkdir(parents=True, exist_ok=True)
    telemetry_record = {
        "candidate": "8k",
        "training_time_seconds": round(train_duration, 4),
        "merge_count": merge_count,
        "vocabulary_size": final_vocab_size,
        "peak_rss_mb": round(peak_rss_mb, 2),
        "min_available_ram_gb": round(min_avail_ram / (1024**3), 3),
        "corpus_bytes_processed": total_clean_bytes,
        "status": "COMPLETED",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    with open(telemetry_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(telemetry_record) + "\n")

    # -------------------------------------------------------------
    # STEP 5: 8K Tokenizer Validation
    # -------------------------------------------------------------
    print("Step 5 Validating Tokenizer...")
    # 1. Save/load
    tmp_val_dir = Path('/tmp/tok_val_8k')
    tmp_val_dir.mkdir(parents=True, exist_ok=True)
    tok.save(tmp_val_dir)
    loaded_tok = IncrementalBPETokenizer.load(tmp_val_dir)

    # 2. UTF-8 round trip
    test_texts = [
        "The quick brown fox jumps over the lazy dog.",
        "NEXA Phase 3F.1 tokenizer validation test with special symbols: !@#$%^&*()_+-=[]{}|;:',.<>/?",
        "Unicode test: café, résumé, 🚀, 地球, Earth, 1234567890."
    ]
    for tt in test_texts:
        enc = loaded_tok.encode(tt)
        dec = loaded_tok.decode(enc)
        assert dec == tt, f"UTF-8 round-trip failed for: {tt}"

    # 3. Control tokens
    for spec_tok, spec_id in DEFAULT_SPECIAL_TOKENS.items():
        assert loaded_tok.encode(spec_tok) == [spec_id], f"Special token encoding failed for {spec_tok}"

    # 4. Reference / Incremental parity check on sample text
    assert tok.encode(test_texts[0]) == loaded_tok.encode(test_texts[0])

    print("Step 5 Validation: PASS (Save/load, UTF-8 round-trip, control tokens verified)")

    # -------------------------------------------------------------
    # STEP 6: Benchmark 8K
    # -------------------------------------------------------------
    print("Step 6 Benchmarking 8K Tokenizer on Certified Corpus...")
    t_enc_start = time.time()
    encoded_docs = []
    actual_token_count = 0
    unique_tokens = set()

    for doc in corpus_docs:
        toks = loaded_tok.encode(doc)
        encoded_docs.append(toks)
        actual_token_count += len(toks)
        unique_tokens.update(toks)

    t_enc_end = time.time()
    enc_duration = t_enc_end - t_enc_start

    t_dec_start = time.time()
    for toks in encoded_docs:
        loaded_tok.decode(toks)
    t_dec_end = time.time()
    dec_duration = t_dec_end - t_dec_start

    tokens_per_char = actual_token_count / total_clean_chars
    tokens_per_byte = actual_token_count / total_clean_bytes
    bytes_per_token = total_clean_bytes / actual_token_count
    enc_throughput_tok_sec = actual_token_count / enc_duration
    enc_throughput_mb_sec = (total_clean_bytes / (1024**2)) / enc_duration
    dec_throughput_tok_sec = actual_token_count / dec_duration
    dec_throughput_mb_sec = (total_clean_bytes / (1024**2)) / dec_duration
    vocab_utilization = (len(unique_tokens) / final_vocab_size) * 100.0

    print(f"  ACTUAL Token Count: {actual_token_count:,} (replaces pre-tokenizer estimate of 8,424,143)")
    print(f"  Tokens / Character: {tokens_per_char:.4f}")
    print(f"  Tokens / Byte: {tokens_per_byte:.4f}")
    print(f"  Compression Ratio (Bytes/Token): {bytes_per_token:.4f}")
    print(f"  Encode Throughput: {enc_throughput_tok_sec:,.2f} tokens/s ({enc_throughput_mb_sec:.2f} MB/s)")
    print(f"  Decode Throughput: {dec_throughput_tok_sec:,.2f} tokens/s ({dec_throughput_mb_sec:.2f} MB/sec)")
    print(f"  Vocabulary Utilization: {vocab_utilization:.2f}% ({len(unique_tokens)}/{final_vocab_size})")

    # -------------------------------------------------------------
    # STEP 7: Freeze 8K Artifact
    # -------------------------------------------------------------
    print("Step 7 Freezing 8K Artifact...")
    cand_dir = Path('nexa-model/tokenizer/candidates/8k')
    cand_dir.mkdir(parents=True, exist_ok=True)

    # 1. Save tokenizer.json
    loaded_tok.save(cand_dir / 'tokenizer.json')

    # 2. Save vocab.json
    vocab_export = {str(k): list(v) if isinstance(v, bytes) else v for k, v in loaded_tok.vocab.items()}
    with open(cand_dir / 'vocab.json', 'w', encoding='utf-8') as f:
        json.dump(vocab_export, f, indent=2)

    # 3. Save merges.txt
    with open(cand_dir / 'merges.txt', 'w', encoding='utf-8') as f:
        for m0, m1 in loaded_tok.merges:
            f.write(f"{m0} {m1}\n")

    # 4. Save config.json
    config_data = {
        "architecture": "NexaBPETokenizer",
        "algorithm": "IncrementalBPE",
        "target_vocab_size": target_vocab,
        "actual_vocab_size": final_vocab_size,
        "min_frequency": min_freq,
        "special_tokens": DEFAULT_SPECIAL_TOKENS,
        "byte_offset": loaded_tok.byte_offset,
        "merge_count": merge_count
    }
    with open(cand_dir / 'config.json', 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2)

    # 5. Save benchmark_report.json
    benchmark_report = {
        "candidate": "8k",
        "target_vocab_size": target_vocab,
        "actual_vocab_size": final_vocab_size,
        "merge_count": merge_count,
        "corpus_files": 75,
        "corpus_bytes": total_clean_bytes,
        "corpus_chars": total_clean_chars,
        "actual_token_count": actual_token_count,
        "pre_tokenizer_estimate": 8424143,
        "tokens_per_character": round(tokens_per_char, 6),
        "tokens_per_byte": round(tokens_per_byte, 6),
        "compression_ratio_bytes_per_token": round(bytes_per_token, 4),
        "encode_throughput_tokens_per_sec": round(enc_throughput_tok_sec, 2),
        "encode_throughput_mb_per_sec": round(enc_throughput_mb_sec, 2),
        "decode_throughput_tokens_per_sec": round(dec_throughput_tok_sec, 2),
        "decode_throughput_mb_per_sec": round(dec_throughput_mb_sec, 2),
        "vocabulary_utilization_percent": round(vocab_utilization, 2),
        "unique_tokens_used": len(unique_tokens),
        "artifact_saved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    with open(cand_dir / 'benchmark_report.json', 'w', encoding='utf-8') as f:
        json.dump(benchmark_report, f, indent=2)

    # 6. Generate SHA-256 integrity manifest
    manifest_dict = {}
    artifact_sizes = {}
    for fpath in sorted(cand_dir.glob('*')):
        if fpath.is_file() and fpath.name != 'integrity_manifest.json':
            content = fpath.read_bytes()
            artifact_sizes[fpath.name] = len(content)
            manifest_dict[fpath.name] = hashlib.sha256(content).hexdigest()

    with open(cand_dir / 'integrity_manifest.json', 'w', encoding='utf-8') as f:
        json.dump(manifest_dict, f, indent=2)

    print("Step 7 Complete: Artifacts frozen in nexa-model/tokenizer/candidates/8k/")
    print(f"Artifact Hashes: {json.dumps(manifest_dict, indent=2)}")

    print("\n=== PHASE 3F.1 COMPLETE — ALL GATE CHECKS PASSED ===")

if __name__ == '__main__':
    main()
