"""
Re-benchmark script for optimized IncrementalBPETokenizer (Phase 3F.1B).
"""

import json
import time
import heapq
import resource
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / "nexa-model"))

from tokenizer.bpe_tokenizer import DEFAULT_SPECIAL_TOKENS
from tokenizer.incremental_bpe import IncrementalBPETokenizer


def get_subset_docs(target_bytes: int) -> List[str]:
    corpus_dir = Path("data/recovery/clean")
    files = sorted(corpus_dir.glob("*.txt"))
    docs = []
    total = 0
    for f in files:
        text = f.read_text(encoding="utf-8")
        b = text.encode("utf-8")
        if total + len(b) > target_bytes and total > 0:
            rem = target_bytes - total
            truncated = b[:rem].decode("utf-8", errors="ignore")
            if truncated:
                docs.append(truncated)
            break
        docs.append(text)
        total += len(b)
        if total >= target_bytes:
            break
    return docs


def benchmark_subset(docs: List[str], target_merges: int = 100) -> dict:
    tokenizer = IncrementalBPETokenizer(vocab_size=256 + 12 + target_merges, min_frequency=2)
    
    t0 = time.perf_counter()
    tokenizer.train(docs)
    t1 = time.perf_counter()

    total_time = t1 - t0
    merges_done = len(tokenizer.merges)
    time_per_100_merges = (total_time / max(1, merges_done)) * 100 if merges_done > 0 else 0.0
    peak_rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0

    return {
        "total_train_time_sec": round(total_time, 4),
        "merges_done": merges_done,
        "time_per_100_merges_sec": round(time_per_100_merges, 4),
        "peak_rss_mb": round(peak_rss_mb, 2),
    }


def main():
    benchmarks = {}
    total_corpus_bytes = 36830981
    num_target_merges_8k = 8000 - 256 - 12 # 7732 merges

    # Load baseline profile if available
    baseline_path = Path("data/reports/phase3f1b_profile.json")
    baseline_data = {}
    if baseline_path.exists():
        with open(baseline_path, "r", encoding="utf-8") as f:
            baseline_data = json.load(f).get("subsets", {})

    for size_mb in [1, 5, 10]:
        target_bytes = size_mb * 1024 * 1024
        docs = get_subset_docs(target_bytes)
        actual_bytes = sum(len(d.encode("utf-8")) for d in docs)
        print(f"Benchmarking optimized trainer on {size_mb} MB ({actual_bytes:,} bytes)...")
        
        res = benchmark_subset(docs, target_merges=100)
        
        time_per_merge = res["total_train_time_sec"] / max(1, res["merges_done"])
        scale_bytes = total_corpus_bytes / max(1, actual_bytes)
        est_full_8k_sec = time_per_merge * scale_bytes * num_target_merges_8k
        
        res["actual_corpus_bytes"] = actual_bytes
        res["estimated_full_8k_36mb_runtime_sec"] = round(est_full_8k_sec, 2)
        res["estimated_full_8k_36mb_runtime_minutes"] = round(est_full_8k_sec / 60.0, 2)

        base_sub = baseline_data.get(f"{size_mb}MB", {})
        if base_sub:
            base_est_hours = base_sub.get("estimated_full_8k_36mb_runtime_hours", 1.0)
            opt_est_hours = est_full_8k_sec / 3600.0
            speedup = base_est_hours / max(0.0001, opt_est_hours)
            res["speedup_vs_baseline"] = f"{speedup:.2f}x"

        benchmarks[f"{size_mb}MB"] = res
        print(f"  Done in {res['total_train_time_sec']}s for {res['merges_done']} merges.")
        print(f"  Time/100 merges: {res['time_per_100_merges_sec']}s | Peak RSS: {res['peak_rss_mb']} MB")
        print(f"  Estimated 36.8MB 8K runtime: {res['estimated_full_8k_36mb_runtime_minutes']} minutes")

    out_data = {
        "phase": "3F.1B",
        "description": "Optimized IncrementalBPETokenizer benchmark report",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "subsets": benchmarks,
        "optimizations_summary": "Doubly-linked array indexing + direct pair occurrence lookup + lazy heap candidate tie-breaking."
    }

    out_path = Path("data/reports/phase3f1b_benchmark.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2)

    print(f"\nSaved benchmark report to {out_path}")


if __name__ == "__main__":
    main()
