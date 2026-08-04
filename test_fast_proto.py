"""
Fixed Prototype test for Doubly Linked List Incremental BPE Tokenizer.
"""

import heapq
import time
import unittest
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "nexa-model"))

from tokenizer.bpe_tokenizer import NexaBPETokenizer, DEFAULT_SPECIAL_TOKENS


class FastIncrementalBPETokenizer(NexaBPETokenizer):
    """
    Optimized Incremental BPE Tokenizer using Doubly Linked List and Pair Occurrence Indexing.
    """

    def train(
        self,
        corpus: Union[str, List[str], Iterable[str]],
        vocab_size: Optional[int] = None,
        min_frequency: Optional[int] = None,
    ) -> None:
        target_vocab_size = vocab_size if vocab_size is not None else self.vocab_size
        min_freq = min_frequency if min_frequency is not None else self.min_frequency

        if isinstance(corpus, str):
            docs = [corpus]
        else:
            docs = list(corpus)

        # 1. Flatten documents into contiguous arrays with doubly-linked pointers
        tokens: List[int] = []
        prev_pos: List[int] = []
        next_pos: List[int] = []

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

        total_tokens = len(tokens)
        if total_tokens < 2:
            self._update_vocab_inv()
            return

        # 2. Build initial pair counts and pair occurrences
        pair_counts: Dict[Tuple[int, int], int] = Counter()
        pair_occurrences: Dict[Tuple[int, int], List[int]] = defaultdict(list)

        for i in range(total_tokens):
            nxt = next_pos[i]
            if nxt != -1:
                pair = (tokens[i], tokens[nxt])
                pair_counts[pair] += 1
                pair_occurrences[pair].append(i)

        next_token_id = self.byte_offset + 256
        if self.vocab:
            next_token_id = max(max(self.vocab.keys()) + 1, next_token_id)

        # Heap items: (-cnt, p0, p1)
        heap = [(-cnt, pair[0], pair[1]) for pair, cnt in pair_counts.items() if cnt >= min_freq]
        heapq.heapify(heap)

        while len(self.vocab) + len(self.special_tokens) < target_vocab_size:
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

            occurrences = pair_occurrences.get(best_pair, [])
            pair_occurrences[best_pair] = []

            for i in occurrences:
                # Validate node i
                if tokens[i] != p0:
                    continue
                j = next_pos[i]
                if j == -1 or tokens[j] != p1:
                    continue

                left = prev_pos[i]
                right = next_pos[j]

                # The pair (p0, p1) itself at (i, j) is being destroyed
                pair_counts[best_pair] -= 1

                # Update left neighbor pair
                if left != -1:
                    p_left = tokens[left]
                    old_left_pair = (p_left, p0)
                    pair_counts[old_left_pair] -= 1
                    c_old_left = pair_counts[old_left_pair]
                    if c_old_left >= min_freq:
                        heapq.heappush(heap, (-c_old_left, p_left, p0))

                    new_left_pair = (p_left, new_id)
                    pair_counts[new_left_pair] += 1
                    c_new_left = pair_counts[new_left_pair]
                    pair_occurrences[new_left_pair].append(left)
                    if c_new_left >= min_freq:
                        heapq.heappush(heap, (-c_new_left, p_left, new_id))

                # Update right neighbor pair
                if right != -1:
                    p_right = tokens[right]
                    old_right_pair = (p1, p_right)
                    pair_counts[old_right_pair] -= 1
                    c_old_right = pair_counts[old_right_pair]
                    if c_old_right >= min_freq:
                        heapq.heappush(heap, (-c_old_right, p1, p_right))

                    new_right_pair = (new_id, p_right)
                    pair_counts[new_right_pair] += 1
                    c_new_right = pair_counts[new_right_pair]
                    pair_occurrences[new_right_pair].append(i)
                    if c_new_right >= min_freq:
                        heapq.heappush(heap, (-c_new_right, new_id, p_right))

                # Mutate node i to new_id
                tokens[i] = new_id
                next_pos[i] = right
                if right != -1:
                    prev_pos[right] = i

                # Invalidate node j
                tokens[j] = -1
                prev_pos[j] = -1
                next_pos[j] = -1

        self._update_vocab_inv()


# Run test comparing FastIncrementalBPETokenizer vs NexaBPETokenizer reference
def test_parity():
    sample_corpus = [
        "The quick brown fox jumps over the lazy dog.",
        "NEXA model tokenizer training for local AI.",
        "Incremental BPE must maintain strict reference parity.",
        "Repeating words: banana banana apple apple cherry cherry.",
    ]
    vocab_size = 350
    min_freq = 2

    ref_tok = NexaBPETokenizer(vocab_size=vocab_size, min_frequency=min_freq)
    ref_tok.train(sample_corpus)

    fast_tok = FastIncrementalBPETokenizer(vocab_size=vocab_size, min_frequency=min_freq)
    fast_tok.train(sample_corpus)

    print(f"Ref merges count: {len(ref_tok.merges)}, Fast merges count: {len(fast_tok.merges)}")
    assert ref_tok.merges == fast_tok.merges, f"MERGES MISMATCH!\nRef:  {ref_tok.merges}\nFast: {fast_tok.merges}"
    assert ref_tok.vocab == fast_tok.vocab, "VOCAB MISMATCH!"

    for doc in sample_corpus:
        assert ref_tok.encode(doc) == fast_tok.encode(doc), f"ENCODE MISMATCH on {doc}"
        assert ref_tok.decode(ref_tok.encode(doc)) == fast_tok.decode(fast_tok.encode(doc)), f"DECODE MISMATCH on {doc}"

    print("ALL PARITY TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_parity()
