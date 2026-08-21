"""
Incremental Byte-Level BPE Tokenizer for NEXA.
RECONSTRUCTED FROM SPECIFICATION (Phase 3F.1C).

Maintains high-performance doubly-linked list token structures with
lazy heap tie-breaking and flat array occurrence pools for strict
memory control (< 2.5 GB RSS), while guaranteeing 100% exact parity with
reference NexaBPETokenizer. Supports restart-safe checkpointing.
"""

import array
import gc
import hashlib
import heapq
import json
import os
import time
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union

try:
    from tokenizer.bpe_tokenizer import NexaBPETokenizer
except ImportError:
    try:
        from .bpe_tokenizer import NexaBPETokenizer
    except ImportError:
        from backend.models.tokenizer.bpe_tokenizer import NexaBPETokenizer

class IncrementalBPETokenizer(NexaBPETokenizer):
    def _get_current_rss_mb(self) -> float:
        try:
            with open('/proc/self/status', 'r') as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        return int(line.split()[1]) / 1024.0
        except Exception:
            pass
        try:
            import resource
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
        except Exception:
            try:
                import psutil
                return psutil.Process().memory_info().rss / (1024.0 * 1024.0)
            except Exception:
                return 0.0

    def _get_available_ram_mb(self) -> float:
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemAvailable:'):
                        return int(line.split()[1]) / 1024.0
        except Exception:
            return 4096.0 # fallback
        return 4096.0

    def train(
        self,
        corpus: Union[str, List[str], Iterable[str]],
        vocab_size: Optional[int] = None,
        min_frequency: Optional[int] = None,
        checkpoint_dir: Optional[Union[str, Path]] = None,
        checkpoint_interval: int = 1000,
        resume: bool = True,
    ) -> None:
        target_vocab_size = vocab_size if vocab_size is not None else self.vocab_size
        min_freq = min_frequency if min_frequency is not None else self.min_frequency

        if isinstance(corpus, str):
            docs = [corpus]
        else:
            docs = list(corpus)

        ckpt_path = Path(checkpoint_dir) if checkpoint_dir else None
        if ckpt_path:
            ckpt_path.mkdir(parents=True, exist_ok=True)

        resumed_step = 0
        if resume and ckpt_path:
            resumed = self._try_resume_checkpoint(ckpt_path)
            if resumed:
                resumed_step = len(self.merges)

        # 1. Flatten documents into contiguous arrays with doubly-linked pointers
        tokens = array.array("i")
        prev_pos = array.array("i")
        next_pos = array.array("i")
        doc_ranges: List[Tuple[int, int]] = []

        for doc in docs:
            if not doc:
                continue
            raw_bytes = doc.encode("utf-8")
            if not raw_bytes:
                continue

            start_idx = len(tokens)
            n_bytes = len(raw_bytes)

            for idx_in_doc, b in enumerate(raw_bytes):
                curr_idx = start_idx + idx_in_doc
                tokens.append(self.byte_offset + b)
                prev_pos.append(curr_idx - 1 if idx_in_doc > 0 else -1)
                next_pos.append(curr_idx + 1 if idx_in_doc < n_bytes - 1 else -1)

            doc_ranges.append((start_idx, start_idx + n_bytes))

        total_tokens = len(tokens)
        if total_tokens < 2:
            self._update_vocab_inv()
            return

        # 2. Build initial pair counts and flat pool pair occurrences
        pair_counts: Dict[Tuple[int, int], int] = Counter()
        pair_head: Dict[Tuple[int, int], int] = {}
        pair_tail: Dict[Tuple[int, int], int] = {}
        occurrences_pool = array.array("i")
        occurrences_next = array.array("i")

        for start_idx, end_idx in doc_ranges:
            for i in range(start_idx, end_idx - 1):
                pair = (tokens[i], tokens[i + 1])
                pair_counts[pair] += 1
                
                pool_idx = len(occurrences_pool)
                occurrences_pool.append(i)
                occurrences_next.append(-1)
                if pair_tail.get(pair, -1) != -1:
                    occurrences_next[pair_tail[pair]] = pool_idx
                else:
                    pair_head[pair] = pool_idx
                pair_tail[pair] = pool_idx

        next_token_id = self.byte_offset + 256
        if self.vocab:
            next_token_id = max(max(self.vocab.keys()) + 1, next_token_id)

        heap = [(-cnt, pair[0], pair[1]) for pair, cnt in pair_counts.items() if cnt >= min_freq]
        heapq.heapify(heap)

        # If resumed, fast-forward existing merges on the tokens
        if resumed_step > 0:
            for m_idx, (p0, p1) in enumerate(self.merges):
                new_id = self.byte_offset + 256 + m_idx
                
                curr_pool_idx = pair_head.get((p0, p1), -1)
                pair_head[(p0, p1)] = -1
                pair_tail[(p0, p1)] = -1
                pair_counts[(p0, p1)] = 0

                while curr_pool_idx != -1:
                    i = occurrences_pool[curr_pool_idx]
                    curr_pool_idx = occurrences_next[curr_pool_idx]

                    if tokens[i] != p0:
                        continue
                    j = next_pos[i]
                    if j == -1 or tokens[j] != p1:
                        continue

                    left = prev_pos[i]
                    right = next_pos[j]

                    if left != -1:
                        p_left = tokens[left]
                        pair_counts[(p_left, p0)] -= 1
                        pair_counts[(p_left, new_id)] += 1
                        
                        pool_idx = len(occurrences_pool)
                        occurrences_pool.append(left)
                        occurrences_next.append(-1)
                        if pair_tail.get((p_left, new_id), -1) != -1:
                            occurrences_next[pair_tail[(p_left, new_id)]] = pool_idx
                        else:
                            pair_head[(p_left, new_id)] = pool_idx
                        pair_tail[(p_left, new_id)] = pool_idx

                    if right != -1:
                        p_right = tokens[right]
                        pair_counts[(p1, p_right)] -= 1
                        pair_counts[(new_id, p_right)] += 1
                        
                        pool_idx = len(occurrences_pool)
                        occurrences_pool.append(i)
                        occurrences_next.append(-1)
                        if pair_tail.get((new_id, p_right), -1) != -1:
                            occurrences_next[pair_tail[(new_id, p_right)]] = pool_idx
                        else:
                            pair_head[(new_id, p_right)] = pool_idx
                        pair_tail[(new_id, p_right)] = pool_idx

                    tokens[i] = new_id
                    next_pos[i] = right
                    if right != -1:
                        prev_pos[right] = i
                    tokens[j] = -1
                    prev_pos[j] = -1
                    next_pos[j] = -1

            heap = [(-cnt, pair[0], pair[1]) for pair, cnt in pair_counts.items() if cnt >= min_freq]
            heapq.heapify(heap)

        # Main merge loop
        while len(self.vocab) + len(self.special_tokens) < target_vocab_size:
            # Memory checks every 50 merges
            merges_count = len(self.merges)
            if merges_count % 50 == 0:
                rss_mb = self._get_current_rss_mb()
                avail_mb = self._get_available_ram_mb()
                
                if rss_mb >= 2500 or avail_mb < 500:
                    print(f"[CRITICAL STOP] RSS: {rss_mb:.2f} MB, Avail RAM: {avail_mb:.2f} MB. Reached safety limit.")
                    if ckpt_path:
                        self._save_checkpoint(ckpt_path, next_token_id)
                    raise MemoryError(f"HARD PROCESS RSS LIMIT REACHED: {rss_mb:.2f} MB or Avail RAM < 500MB")
                elif rss_mb >= 2400 or avail_mb < 750:
                    print(f"[WARNING] RSS: {rss_mb:.2f} MB, Avail RAM: {avail_mb:.2f} MB. Forcing GC and Checkpoint.")
                    gc.collect()
                    if ckpt_path:
                        self._save_checkpoint(ckpt_path, next_token_id)
                elif rss_mb >= 2200:
                    gc.collect()

            best_pair = None
            best_count = -1

            while heap:
                neg_cnt, p0, p1 = heapq.heappop(heap)
                cnt = -neg_cnt
                pair = (p0, p1)
                actual_cnt = pair_counts.get(pair, 0)
                if actual_cnt >= min_freq and actual_cnt == cnt:
                    best_pair = pair
                    best_count = cnt
                    break

            if best_pair is None or best_count < min_freq:
                break

            p0, p1 = best_pair
            new_id = next_token_id
            next_token_id += 1

            self.merges.append(best_pair)
            self.merge_ranks[best_pair] = len(self.merges) - 1
            self.vocab[new_id] = self.vocab[p0] + self.vocab[p1]

            if merges_count % 1000 == 0 or len(self.vocab) + len(self.special_tokens) >= target_vocab_size:
                rss = self._get_current_rss_mb()
                print(
                    f"  [IncrementalBPE] Merges: {merges_count} | Current Vocab: {len(self.vocab) + len(self.special_tokens)}/{target_vocab_size} | RSS: {rss:.2f} MB"
                )
                if ckpt_path and (merges_count % checkpoint_interval == 0):
                    self._save_checkpoint(ckpt_path, next_token_id)

            curr_pool_idx = pair_head.get(best_pair, -1)
            pair_head[best_pair] = -1
            pair_tail[best_pair] = -1
            
            modified_pairs: Set[Tuple[int, int]] = set()

            while curr_pool_idx != -1:
                i = occurrences_pool[curr_pool_idx]
                curr_pool_idx = occurrences_next[curr_pool_idx]

                if tokens[i] != p0:
                    continue
                j = next_pos[i]
                if j == -1 or tokens[j] != p1:
                    continue

                left = prev_pos[i]
                right = next_pos[j]

                pair_counts[best_pair] -= 1

                if left != -1:
                    p_left = tokens[left]
                    old_left_pair = (p_left, p0)
                    pair_counts[old_left_pair] -= 1
                    modified_pairs.add(old_left_pair)

                    new_left_pair = (p_left, new_id)
                    pair_counts[new_left_pair] += 1
                    modified_pairs.add(new_left_pair)
                    
                    pool_idx = len(occurrences_pool)
                    occurrences_pool.append(left)
                    occurrences_next.append(-1)
                    if pair_tail.get(new_left_pair, -1) != -1:
                        occurrences_next[pair_tail[new_left_pair]] = pool_idx
                    else:
                        pair_head[new_left_pair] = pool_idx
                    pair_tail[new_left_pair] = pool_idx

                if right != -1:
                    p_right = tokens[right]
                    old_right_pair = (p1, p_right)
                    pair_counts[old_right_pair] -= 1
                    modified_pairs.add(old_right_pair)

                    new_right_pair = (new_id, p_right)
                    pair_counts[new_right_pair] += 1
                    modified_pairs.add(new_right_pair)

                    pool_idx = len(occurrences_pool)
                    occurrences_pool.append(i)
                    occurrences_next.append(-1)
                    if pair_tail.get(new_right_pair, -1) != -1:
                        occurrences_next[pair_tail[new_right_pair]] = pool_idx
                    else:
                        pair_head[new_right_pair] = pool_idx
                    pair_tail[new_right_pair] = pool_idx

                tokens[i] = new_id
                next_pos[i] = right
                if right != -1:
                    prev_pos[right] = i

                tokens[j] = -1
                prev_pos[j] = -1
                next_pos[j] = -1

            for pair in modified_pairs:
                cnt = pair_counts.get(pair, 0)
                if cnt >= min_freq:
                    heapq.heappush(heap, (-cnt, pair[0], pair[1]))
            
            # Periodically compact the pool to prevent memory growth (if pool > 150M elements -> ~600MB each)
            if len(occurrences_pool) > 150_000_000:
                print(f"[MEMORY OPTIMIZATION] occurrences_pool size {len(occurrences_pool)} exceeded threshold. Compacting...")
                self._compact_pool(pair_head, pair_tail, occurrences_pool, occurrences_next, tokens)
                gc.collect()

        if ckpt_path and len(self.merges) > 0:
            self._save_checkpoint(ckpt_path, next_token_id, is_final=True)

        self._update_vocab_inv()

    def _compact_pool(self, pair_head, pair_tail, occurrences_pool, occurrences_next, tokens):
        new_pool = array.array("i")
        new_next = array.array("i")
        
        # Traverse pair_head and rebuild pool without stale entries
        for pair, head_idx in list(pair_head.items()):
            if head_idx == -1:
                continue
            
            new_head = -1
            new_tail = -1
            curr = head_idx
            
            # Traverse occurrences for this pair
            while curr != -1:
                i = occurrences_pool[curr]
                curr = occurrences_next[curr]
                
                # Check if occurrence is still valid
                if tokens[i] != pair[0]:
                    continue
                # We can't trivially check the right token without next_pos, 
                # but removing definitely invalid ones (tokens[i] changed) is good enough.
                
                # Add valid occurrence to new pool
                idx = len(new_pool)
                new_pool.append(i)
                new_next.append(-1)
                
                if new_tail != -1:
                    new_next[new_tail] = idx
                else:
                    new_head = idx
                new_tail = idx
                
            pair_head[pair] = new_head
            pair_tail[pair] = new_tail
            
        occurrences_pool[:] = new_pool
        occurrences_next[:] = new_next

    def _save_checkpoint(self, ckpt_dir: Path, next_token_id: int, is_final: bool = False) -> None:
        step = len(self.merges)
        filename = "checkpoint_final.json" if is_final else f"checkpoint_step_{step}.json"
        target_file = ckpt_dir / filename

        vocab_serializable = {str(k): list(v) for k, v in self.vocab.items()}
        merges_serializable = [list(m) for m in self.merges]

        payload = {
            "step": step,
            "next_token_id": next_token_id,
            "merges": merges_serializable,
            "vocab": vocab_serializable,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        content_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        checksum = hashlib.sha256(content_bytes).hexdigest()
        payload["checksum"] = checksum

        tmp_file = ckpt_dir / f"{filename}.tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        tmp_file.replace(target_file)

        # Cleanup old checkpoints
        if not is_final:
            all_ckpts = sorted(ckpt_dir.glob("checkpoint_step_*.json"), key=lambda p: int(p.stem.split("_")[-1]))
            # keep last 2
            for old_ckpt in all_ckpts[:-2]:
                try:
                    old_ckpt.unlink()
                except Exception:
                    pass

    def _try_resume_checkpoint(self, ckpt_dir: Path) -> bool:
        ckpt_files = sorted(ckpt_dir.glob("checkpoint_step_*.json"), key=lambda p: int(p.stem.split("_")[-1])) + sorted(ckpt_dir.glob("checkpoint_final.json"))
        if not ckpt_files:
            return False

        latest_file = ckpt_files[-1]
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            recorded_checksum = data.get("checksum")
            data_copy = dict(data)
            data_copy.pop("checksum", None)
            expected_checksum = hashlib.sha256(json.dumps(data_copy, sort_keys=True).encode("utf-8")).hexdigest()

            if recorded_checksum != expected_checksum:
                print(f"[Checkpoint Warning] Corrupted checksum in {latest_file.name}, skipping resume.")
                return False

            self.merges = [tuple(m) for m in data["merges"]]
            self.merge_ranks = {m: i for i, m in enumerate(self.merges)}
            self.vocab = {int(k): bytes(v) for k, v in data["vocab"].items()}
            self._update_vocab_inv()
            print(f"[Checkpoint Resume] Successfully resumed from {latest_file.name} at step {data['step']}.")
            return True
        except Exception as e:
            print(f"[Checkpoint Error] Failed to load {latest_file}: {e}")
            return False
