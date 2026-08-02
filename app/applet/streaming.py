"""Streaming generation helper for NEXA Chat Engine."""
import torch
import torch.nn.functional as F
from typing import Generator, Tuple, Optional, List

class TokenStreamer:
    """Helper class to manage streaming token generation and incremental text decoding."""
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.generated_tokens: List[int] = []
        self.decoded_cache: str = ""

    def process_token(self, token_id: int) -> Tuple[str, str]:
        """
        Processes a newly generated token ID, appends to generated tokens,
        and returns (incremental_text, full_text).
        """
        self.generated_tokens.append(token_id)
        full_text = self.tokenizer.decode(self.generated_tokens)
        incremental_text = full_text[len(self.decoded_cache):]
        self.decoded_cache = full_text
        return incremental_text, full_text
