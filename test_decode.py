import numpy as np
import sys
sys.path.append('nexa-model')
from tokenizer.bpe_tokenizer import NexaBPETokenizer

tok = NexaBPETokenizer.load('nexa-model/tokenizer/production/tokenizer.json')
tokens = np.fromfile('data/shards/pd5m_v7_8k/train/doc_0.bin', dtype=np.uint16).tolist()
tokens = [t if t < 8000 else 0 for t in tokens]  # Replace 49135 with 0 or drop them
print(tok.decode(tokens[:100]))
