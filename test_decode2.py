import numpy as np
import sys
sys.path.append('nexa-model')
from tokenizer.bpe_tokenizer import NexaBPETokenizer

tok = NexaBPETokenizer.load('nexa-model/tokenizer/production/tokenizer.json')
# Read as uint16 big endian, then convert to little endian?
# If the file was written as big-endian, we read it as >u2
tokens = np.fromfile('data/shards/pd5m_v7_8k/train/doc_0.bin', dtype='>u2').tolist()
# Filter out out-of-bounds tokens
tokens = [t if t < 8000 else 0 for t in tokens]
print(tok.decode(tokens[:100]))
