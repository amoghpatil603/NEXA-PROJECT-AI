import sys, array
sys.path.append('nexa-model')
from tokenizer.bpe_tokenizer import NexaBPETokenizer

tok = NexaBPETokenizer.load('nexa-model/tokenizer/production/tokenizer.json')
with open('data/recovery/clean/1.txt', 'r') as f: text = f.read()

def fast_encode_chunk(self, chunk: str) -> list[int]:
    pass # we don't need it, we can just use original

encoded = tok.encode(text)[:20]
print("True tokens:", encoded)

arr = array.array("H", encoded)
true_bytes = arr.tobytes()
print("True bytes:", true_bytes)

with open('data/shards/pd5m_v7_8k/train/doc_0.bin', 'rb') as f:
    disk_bytes = f.read(40)
print("Disk bytes:", disk_bytes)

