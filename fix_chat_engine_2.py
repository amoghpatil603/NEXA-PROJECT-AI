import sys
content = open("backend/models/chat_engine.py").read()

import re
match = re.search(r"from model\.config import NexaConfig.*?from tokenizer\.incremental_bpe import IncrementalBPETokenizer", content, re.DOTALL)
if match:
    rep = """try:
    from model.config import NexaConfig
    from model.transformer import NexaTransformer
    from training.checkpoint import load_checkpoint
    from tokenizer.bpe_tokenizer import DEFAULT_SPECIAL_TOKENS
    from tokenizer.incremental_bpe import IncrementalBPETokenizer
except ImportError:
    NexaConfig = None
    NexaTransformer = None
    load_checkpoint = None
    DEFAULT_SPECIAL_TOKENS = {'<PAD>': 0}
    IncrementalBPETokenizer = None"""
    content = content.replace(match.group(0), rep)

open("backend/models/chat_engine.py", "w").write(content)
