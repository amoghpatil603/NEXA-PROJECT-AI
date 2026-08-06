"""
Profiling script for original IncrementalBPETokenizer.
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

from tokenizer.bpe_tokenizer import NexaBPETokenizer, DEFAULT_SPECIAL_TOKENS


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


def profile_current_trainer(corpus: List[str], target_merges: int = 30) -> dict:
    byte_offset = max(DEFAULT_SPECIAL_TOKENS.values()) + 1
    
    # 1. Initialization
    t0 = time.perf_counter()
    doc_tokens: List[List[int]] = []
    for doc in corpus:
        if not doc:
            continue
        raw_bytes = doc.encode("utf-8")
        tok_ids = [byte_offset + b for b in raw_bytes]
        doc_tokens.append(tok_ids)
    t1 = time.perf_counter()
    init_time = t1 - t0

    # 2. Pair count construction
    pair_counts: Dict[Tuple[int, int], int] = Counter()
    pair_to_docs: Dict[Tuple[int, int], Set[int]] = defaultdict(set)
    for doc_idx, doc in enumerate(doc_tokens):
        for i in range(len(doc) - 1):
            pair = (doc[i], doc[i + 1])
            pair_counts[pair] += 1
            pair_to_docs[pair].add(doc_idx)
    t2 = time.perf_counter()
    pair_construct_time = t2 - t1

    heap = [(-cnt, pair) for pair, cnt in pair_counts.items() if cnt >= 2]
    heapq.heapify(heap)

    heap_selection_time = 0.0
    merge_app_time = 0.0
    pair_update_time = 0.0
    merges_done = 0

    next_token_id = byte_offset + 256

    t_start_merges = time.perf_counter()

    for m in range(target_merges):
        # Heap selection
        th0 = time.perf_counter()
        best_pair = None
        best_count = -1
        while heap:
            neg_cnt, pair = heapq.heappop(heap)
            cnt = -neg_cnt
            actual_cnt = pair_counts.get(pair, 0)
            if actual_cnt >= 2 and actual_cnt == cnt:
                best_pair = pair
                best_count = cnt
                break
        th1 = time.perf_counter()
        heap_selection_time += (th1 - th0)

        if best_pair is None:
            break

        new_id = next_token_id
        next_token_id += 1
        p0, p1 = best_pair

        # Merge application
        tm0 = time.perf_counter()
        changed_pairs: Set[Tuple[int, int]] = set()
        affected_doc_indices = list(pair_to_docs.get(best_pair, set()))

        for doc_idx in affected_doc_indices:
            doc = doc_tokens[doc_idx]
            n_doc = len(doc)
            if n_doc < 2:
                continue

            match_indices: List[int] = []
            idx = 0
            while idx < n_doc - 1:
                if doc[idx] == p0 and doc[idx + 1] == p1:
                    match_indices.append(idx)
                    idx += 2
                else:
                    idx += 1

            if not match_indices:
                pair_to_docs[best_pair].discard(doc_idx)
                continue

            new_doc: List[int] = []
            last_idx = 0
            for m_idx in match_indices:
                if m_idx > last_idx:
                    new_doc.extend(doc[last_idx:m_idx])

                p_left = new_doc[-1] if new_doc else None
                p_right = doc[m_idx + 2] if m_idx + 2 < n_doc else None

                if p_left is not None:
                    pair_counts[(p_left, p0)] -= 1
                    changed_pairs.add((p_left, p0))
                    pair_counts[(p_left, new_id)] = pair_counts.get((p_left, new_id), 0) + 1
                    changed_pairs.add((p_left, new_id))
                    pair_to_docs[(p_left, new_id)].add(doc_idx)

                pair_counts[(p0, p1)] -= 1
                changed_pairs.add((p0, p1))

                if p_right is not None:
                    pair_counts[(p1, p_right)] -= 1
                    changed_pairs.add((p1, p_right))
                    pair_counts[(new_id, p_right)] = pair_counts.get((new_id, p_right), 0) + 1
                    changed_pairs.add((new_id, p_right))
                    pair_to_docs[(new_id, p_right)].add(doc_idx)

                new_doc.append(new_id)
                last_idx = m_idx + 2

            if last_idx < n_doc:
                new_doc.extend(doc[last_idx:])

            doc_tokens[doc_idx] = new_doc

        tm1 = time.perf_counter()
        merge_app_time += (tm1 - tm0)

        # Pair frequency updates
        tp0 = time.perf_counter()
        for pair in changed_pairs:
            cnt = pair_counts.get(pair, 0)
            if cnt <= 0:
                pair_counts.pop(pair, None)
                pair_to_docs.pop(pair, None)
            elif cnt >= 2:
                heapq.heappush(heap, (-cnt, pair))
        tp1 = time.perf_counter()
        pair_update_time += (tp1 - tp0)

        merges_done += 1

    t_end_merges = time.perf_counter()
    total_merge_phase_time = t_end_merges - t_start_merges
    time_per_100_merges = (total_merge_phase_time / max(1, merges_done)) * 100 if merges_done > 0 else 0.0

    peak_rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0

    return {
        "initialization_time_sec": round(init_time, 4),
        "pair_count_construction_time_sec": round(pair_construct_time, 4),
        "merges_profiled": merges_done,
        "total_merge_phase_time_sec": round(total_merge_phase_time, 4),
        "time_per_100_merges_sec": round(time_per_100_merges, 4),
        "heap_selection_overhead_sec": round(heap_selection_time, 4),
        "merge_application_time_sec": round(merge_app_time, 4),
        "pair_frequency_update_time_sec": round(pair_update_time, 4),
        "peak_rss_mb": round(peak_rss_mb, 2),
    }


def main():
    profile_results = {}
    total_corpus_bytes = 36830981
    num_target_merges_8k = 8000 - 256 - 12 # approx 7732 merges

    for size_mb in [1, 5, 10]:
        target_bytes = size_mb * 1024 * 1024
        docs = get_subset_docs(target_bytes)
        actual_bytes = sum(len(d.encode("utf-8")) for d in docs)
        print(f"Profiling original trainer on {size_mb} MB ({actual_bytes:,} bytes)...")
        
        prof = profile_current_trainer(docs, target_merges=30)
        
        # Estimate full 8K runtime on 36.8 MB corpus
        time_per_merge = prof["total_merge_phase_time_sec"] / max(1, prof["merges_profiled"])
        scale_bytes = total_corpus_bytes / max(1, actual_bytes)
        est_full_8k_sec = time_per_merge * scale_bytes * num_target_merges_8k
        
        prof["actual_corpus_bytes"] = actual_bytes
        prof["estimated_full_8k_36mb_runtime_sec"] = round(est_full_8k_sec, 2)
        prof["estimated_full_8k_36mb_runtime_hours"] = round(est_full_8k_sec / 3600.0, 2)
        
        profile_results[f"{size_mb}MB"] = prof
        print(f"  Done in {prof['total_merge_phase_time_sec']}s for {prof['merges_profiled']} merges.")
        print(f"  Time/100 merges: {prof['time_per_100_merges_sec']}s | Merge app time: {prof['merge_application_time_sec']}s")
        print(f"  Estimated 36.8MB 8K runtime: {prof['estimated_full_8k_36mb_runtime_hours']} hours")

    report_data = {
        "phase": "3F.1B",
        "description": "Original IncrementalBPETokenizer profiling report",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "subsets": profile_results,
        "primary_bottleneck": "List recreation, linear doc search, and dict pair management during merge application phase."
    }

    out_path = Path("data/reports/phase3f1b_profile.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    print(f"\nSaved profile report to {out_path}")


if __name__ == "__main__":
    main()
