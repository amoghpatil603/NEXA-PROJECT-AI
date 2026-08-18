import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path("nexa-model").resolve()))
from tokenizer.incremental_bpe import IncrementalBPETokenizer

tok = IncrementalBPETokenizer.load("nexa-model/tokenizer/production/tokenizer.json")
encoded = tok.encode("Hello world!")
decoded = tok.decode(encoded)
print("Vocab size:", len(tok.vocab) + len(tok.special_tokens))
print("Decoded:", decoded)
