"""
Reference Byte-Level BPE Tokenizer for NEXA.
RECONSTRUCTED FROM SPECIFICATION (Phase R1).
"""

import json
import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union

DEFAULT_SPECIAL_TOKENS: Dict[str, int] = {
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


class NexaBPETokenizer:
    """
    Byte-level BPE Tokenizer for NEXA model.

    Key properties:
    - Byte-level base vocabulary (256 bytes)
    - Deterministic pair frequency counting and tie-breaking
    - Strict document boundary protection (no pairs across documents)
    - Unicode-safe encode/decode round trip
    - Save/Load serialization
    """

    def __init__(
        self,
        vocab_size: int = 8000,
        min_frequency: int = 2,
        special_tokens: Optional[Union[Dict[str, int], List[str]]] = None,
    ):
        self.vocab_size = vocab_size
        self.min_frequency = min_frequency

        # Setup special tokens
        if special_tokens is None:
            self.special_tokens = dict(DEFAULT_SPECIAL_TOKENS)
        elif isinstance(special_tokens, dict):
            self.special_tokens = dict(special_tokens)
        elif isinstance(special_tokens, list):
            self.special_tokens = {tok: idx for idx, tok in enumerate(special_tokens)}
        else:
            raise ValueError("special_tokens must be a dict or list")

        self.special_tokens_inv: Dict[int, str] = {
            v: k for k, v in self.special_tokens.items()
        }

        # Offset for base 256 byte tokens
        max_special_id = max(self.special_tokens.values()) if self.special_tokens else -1
        self.byte_offset = max_special_id + 1

        # Initialize base byte vocabulary
        self.vocab: Dict[int, bytes] = {}
        for b in range(256):
            self.vocab[self.byte_offset + b] = bytes([b])

        self.merges: List[Tuple[int, int]] = []
        self.merge_ranks: Dict[Tuple[int, int], int] = {}
        self._update_vocab_inv()

    def _update_vocab_inv(self) -> None:
        self.vocab_inv: Dict[bytes, int] = {v: k for k, v in self.vocab.items()}

    def train(
        self,
        corpus: Union[str, List[str], Iterable[str]],
        vocab_size: Optional[int] = None,
        min_frequency: Optional[int] = None,
    ) -> None:
        """
        Train byte-level BPE on a corpus of document strings.
        Ensures document boundaries do not create cross-document pairs.
        """
        target_vocab_size = vocab_size if vocab_size is not None else self.vocab_size
        min_freq = min_frequency if min_frequency is not None else self.min_frequency

        if isinstance(corpus, str):
            docs = [corpus]
        else:
            docs = list(corpus)

        # Tokenize documents into initial byte token IDs
        doc_tokens: List[List[int]] = []
        for doc in docs:
            if not doc:
                continue
            raw_bytes = doc.encode("utf-8")
            doc_tokens.append([self.byte_offset + b for b in raw_bytes])

        next_token_id = self.byte_offset + 256
        if self.vocab:
            next_token_id = max(max(self.vocab.keys()) + 1, next_token_id)

        while len(self.vocab) + len(self.special_tokens) < target_vocab_size:
            # Count pair frequencies across all documents independently
            pair_counts: Dict[Tuple[int, int], int] = {}
            for doc in doc_tokens:
                for i in range(len(doc) - 1):
                    pair = (doc[i], doc[i + 1])
                    pair_counts[pair] = pair_counts.get(pair, 0) + 1

            if not pair_counts:
                break

            # Find best pair with deterministic tie-breaking:
            # (-freq, pair[0], pair[1]) ensures highest frequency first, then lowest token IDs.
            best_pair = None
            best_count = -1

            for pair, count in pair_counts.items():
                if count < min_freq:
                    continue
                if count > best_count:
                    best_count = count
                    best_pair = pair
                elif count == best_count:

                    # Deterministic tie-breaker
                    if best_pair is None or pair < best_pair:
                        best_pair = pair

            if best_pair is None or best_count < min_freq:
                break

            # Register new token and merge
            new_id = next_token_id
            next_token_id += 1

            p0, p1 = best_pair
            self.merges.append(best_pair)
            self.merge_ranks[best_pair] = len(self.merges) - 1
            self.vocab[new_id] = self.vocab[p0] + self.vocab[p1]

            # Substitute best_pair in all document token sequences
            new_doc_tokens: List[List[int]] = []
            for doc in doc_tokens:
                i = 0
                new_doc: List[int] = []
                while i < len(doc):
                    if i < len(doc) - 1 and doc[i] == p0 and doc[i + 1] == p1:
                        new_doc.append(new_id)
                        i += 2
                    else:
                        new_doc.append(doc[i])
                        i += 1
                new_doc_tokens.append(new_doc)
            doc_tokens = new_doc_tokens

        self._update_vocab_inv()

    def encode(self, text: str) -> List[int]:
        """
        Encode text into a list of token IDs.
        Supports special tokens embedded in text if matched.
        """
        if not text:
            return []

        # Check for special tokens in text
        tokens: List[int] = []
        i = 0
        while i < len(text):
            matched_special = False
            for spec_tok, spec_id in self.special_tokens.items():
                if text.startswith(spec_tok, i):
                    tokens.append(spec_id)
                    i += len(spec_tok)
                    matched_special = True
                    break

            if not matched_special:
                # Accumulate non-special text up to next special token
                next_spec_idx = len(text)
                for spec_tok in self.special_tokens.keys():
                    idx = text.find(spec_tok, i)
                    if idx != -1 and idx < next_spec_idx:
                        next_spec_idx = idx

                segment = text[i:next_spec_idx]
                if segment:
                    tokens.extend(self._encode_chunk(segment))
                i = next_spec_idx

        return tokens

    def _encode_chunk(self, chunk: str) -> List[int]:

        raw_bytes = chunk.encode("utf-8")
        if not raw_bytes:
            return []
        tokens = [self.byte_offset + b for b in raw_bytes]

        if not self.merge_ranks:
            return tokens

        while len(tokens) >= 2:

            # Find pairs with minimum merge rank
            min_rank = float("inf")
            best_idx = -1

            for idx in range(len(tokens) - 1):
                pair = (tokens[idx], tokens[idx + 1])
                rank = self.merge_ranks.get(pair)
                if rank is not None and rank < min_rank:
                    min_rank = rank
                    best_idx = idx

            if best_idx == -1:
                break

            pair = (tokens[best_idx], tokens[best_idx + 1])
            p0, p1 = pair
            # Determine new_id from merges or vocab
            new_id = None
            merged_bytes = self.vocab[p0] + self.vocab[p1]
            new_id = self.vocab_inv.get(merged_bytes)

            if new_id is None:
                break

            tokens = tokens[:best_idx] + [new_id] + tokens[best_idx + 2 :]

        return tokens

    def decode(self, tokens: List[int]) -> str:
        """
        Decode a list of token IDs back into a string.
        """
        byte_chunks: List[bytes] = []
        for t in tokens:
            if t in self.special_tokens_inv:
                byte_chunks.append(self.special_tokens_inv[t].encode("utf-8"))
            elif t in self.vocab:
                byte_chunks.append(self.vocab[t])
            else:
                # Unknown token fallback
                unk_str = self.special_tokens_inv.get(3, "<UNK>")
                byte_chunks.append(unk_str.encode("utf-8"))

        full_bytes = b"".join(byte_chunks)
        return full_bytes.decode("utf-8", errors="replace")

    def save(self, path_or_dir: Union[str, Path]) -> None:
        """
        Save tokenizer configuration and state to JSON file.
        """
        p = Path(path_or_dir)
        if p.is_dir() or not p.name.endswith(".json"):
            p.mkdir(parents=True, exist_ok=True)
            file_path = p / "tokenizer.json"
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            file_path = p

        data = {
            "vocab_size": self.vocab_size,
            "min_frequency": self.min_frequency,
            "special_tokens": self.special_tokens,
            "byte_offset": self.byte_offset,
            "merges": [list(m) for m in self.merges],
            "vocab": {str(k): list(v) for k, v in self.vocab.items()},
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path_or_dir: Union[str, Path]) -> "NexaBPETokenizer":
        """
        Load tokenizer configuration and state from JSON file.
        """
        p = Path(path_or_dir)
        if p.is_dir():
            file_path = p / "tokenizer.json"
        else:
            file_path = p

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        tok = cls(
            vocab_size=data["vocab_size"],
            min_frequency=data["min_frequency"],
            special_tokens=data["special_tokens"],
        )

        tok.byte_offset = data.get("byte_offset", tok.byte_offset)
        tok.vocab = {int(k): bytes(v) for k, v in data["vocab"].items()}
        tok.merges = [tuple(m) for m in data["merges"]]
        tok.merge_ranks = {tuple(m): idx for idx, m in enumerate(tok.merges)}
        tok._update_vocab_inv()
        return tok
