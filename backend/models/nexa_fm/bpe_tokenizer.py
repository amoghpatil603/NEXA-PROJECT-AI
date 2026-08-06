import json
import re
import os
from typing import List, Dict, Tuple, Optional, Iterator

class NexaBPETokenizer:
    """
    Byte-Pair Encoding (BPE) Tokenizer for the NEXA Foundation Model.
    Operates directly on UTF-8 bytes to ensure full Unicode support without <UNK> tokens.
    """
    def __init__(self, vocab_size: int = 8192):
        self.vocab_size = vocab_size
        self.special_tokens = {
            "<PAD>": 0,
            "<BOS>": 1,
            "<EOS>": 2,
            "<UNK>": 3,
            "<MASK>": 4
        }
        
        self.base_vocab_size = 256
        self.special_tokens_size = len(self.special_tokens)
        self.merge_offset = self.base_vocab_size + self.special_tokens_size
        
        self.merges: Dict[Tuple[int, int], int] = {}
        self.vocab: Dict[int, bytes] = {}
        
        # Regex for splitting words
        self.pat = re.compile(r"""'s|'t|'re|'ve|'m|'ll|'d| ?[A-Za-z]+| ?[0-9]+| ?[^\sA-Za-z0-9]+|\s+(?!\S)|\s+""")
        
        self._build_vocab()

    def _build_vocab(self):
        self.vocab = {}
        for k, v in self.special_tokens.items():
            self.vocab[v] = k.encode('utf-8')
        for i in range(256):
            self.vocab[i + self.special_tokens_size] = bytes([i])
        for (p0, p1), idx in self.merges.items():
            self.vocab[idx] = self.vocab[p0] + self.vocab[p1]

    def _get_stats(self, words: List[List[int]]) -> Dict[Tuple[int, int], int]:
        counts = {}
        for word in words:
            for pair in zip(word, word[1:]):
                counts[pair] = counts.get(pair, 0) + 1
        return counts

    def _merge_vocab(self, words: List[List[int]], pair: Tuple[int, int], new_id: int) -> List[List[int]]:
        new_words = []
        for word in words:
            new_word = []
            i = 0
            while i < len(word):
                if i < len(word) - 1 and word[i] == pair[0] and word[i+1] == pair[1]:
                    new_word.append(new_id)
                    i += 2
                else:
                    new_word.append(word[i])
                    i += 1
            new_words.append(new_word)
        return new_words

    def train(self, text_iterator: Iterator[str], target_vocab_size: Optional[int] = None):
        if target_vocab_size is not None:
            self.vocab_size = target_vocab_size
            
        num_merges = self.vocab_size - self.base_vocab_size - self.special_tokens_size
        if num_merges <= 0:
            return
            
        words = []
        for text in text_iterator:
            for match in re.findall(self.pat, text):
                words.append([b + self.special_tokens_size for b in match.encode('utf-8')])
                
        for i in range(num_merges):
            stats = self._get_stats(words)
            if not stats:
                break
            best_pair = max(stats, key=stats.get)
            new_id = self.merge_offset + i
            self.merges[best_pair] = new_id
            words = self._merge_vocab(words, best_pair, new_id)
            
        self._build_vocab()

    def encode(self, text: str, add_special_tokens: bool = False) -> List[int]:
        tokens = []
        if add_special_tokens:
            tokens.append(self.special_tokens["<BOS>"])
            
        for match in re.findall(self.pat, text):
            word_tokens = [b + self.special_tokens_size for b in match.encode('utf-8')]
            
            while len(word_tokens) >= 2:
                stats = self._get_stats([word_tokens])
                if not stats:
                    break
                pair = min(stats.keys(), key=lambda p: self.merges.get(p, float('inf')))
                if pair not in self.merges:
                    break
                idx = self.merges[pair]
                word_tokens = self._merge_vocab([word_tokens], pair, idx)[0]
                
            tokens.extend(word_tokens)
            
        if add_special_tokens:
            tokens.append(self.special_tokens["<EOS>"])
            
        return tokens

    def decode(self, tokens: List[int], skip_special_tokens: bool = True) -> str:
        b = bytearray()
        for t in tokens:
            if t in self.vocab:
                if skip_special_tokens and t < self.special_tokens_size:
                    continue
                val = self.vocab[t]
                b.extend(val)
            else:
                if not skip_special_tokens:
                    b.extend(self.vocab.get(self.special_tokens["<UNK>"], b""))
        return b.decode('utf-8', errors='replace')

    def save(self, filepath: str):
        merges_str = {f"{p0},{p1}": idx for (p0, p1), idx in self.merges.items()}
        data = {
            "vocab_size": self.vocab_size,
            "special_tokens": self.special_tokens,
            "merges": merges_str
        }
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> "NexaBPETokenizer":
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        tokenizer = cls(vocab_size=data.get("vocab_size", 8192))
        tokenizer.special_tokens = data.get("special_tokens", {})
        
        merges = {}
        for k, v in data.get("merges", {}).items():
            p0, p1 = k.split(',')
            merges[(int(p0), int(p1))] = v
        tokenizer.merges = merges
        tokenizer._build_vocab()
        return tokenizer
