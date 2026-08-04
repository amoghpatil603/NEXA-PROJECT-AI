import sys, heapq
sys.path.append('nexa-model')
from tokenizer.bpe_tokenizer import NexaBPETokenizer

tok1 = NexaBPETokenizer.load('nexa-model/tokenizer/production/tokenizer.json')

with open('data/recovery/clean/1.txt', 'r') as f: text = f.read()

# Original O(N^2) tokenizer
encoded1 = tok1.encode(text)

# Now monkey patched tokenizer
def fast_encode_chunk(self, chunk: str) -> list[int]:
    raw_bytes = chunk.encode("utf-8")
    if not raw_bytes: return []
    nodes = []
    for i, b in enumerate(raw_bytes): nodes.append([i - 1, i + 1, self.byte_offset + b, None])
    nodes[0][0] = -1; nodes[-1][1] = -1
    if not self.merge_ranks: return [n[2] for n in nodes]
    pq = []
    for i in range(len(nodes) - 1):
        t1, t2 = nodes[i][2], nodes[i+1][2]
        rank = self.merge_ranks.get((t1, t2))
        nodes[i][3] = rank
        if rank is not None: heapq.heappush(pq, (rank, i))
    while pq:
        rank, i = heapq.heappop(pq)
        node = nodes[i]
        if node[2] == -1 or node[3] != rank: continue
        nxt = node[1]
        nxt_node = nodes[nxt]
        t1, t2 = node[2], nxt_node[2]
        merged_bytes = self.vocab[t1] + self.vocab[t2]
        new_id = self.vocab_inv.get(merged_bytes)
        if new_id is None: continue
        node[2] = new_id
        node[1] = nxt_node[1]; node[3] = None
        if nxt_node[1] != -1: nodes[nxt_node[1]][0] = i
        nxt_node[2] = -1
        prev = node[0]
        if prev != -1:
            prev_node = nodes[prev]
            new_rank = self.merge_ranks.get((prev_node[2], node[2]))
            prev_node[3] = new_rank
            if new_rank is not None: heapq.heappush(pq, (new_rank, prev))
        nxt2 = node[1]
        if nxt2 != -1:
            new_rank = self.merge_ranks.get((node[2], nodes[nxt2][2]))
            node[3] = new_rank
            if new_rank is not None: heapq.heappush(pq, (new_rank, i))
    tokens = []
    curr = 0
    while curr != -1:
        tokens.append(nodes[curr][2])
        curr = nodes[curr][1]
    return tokens

NexaBPETokenizer._encode_chunk = fast_encode_chunk
tok2 = NexaBPETokenizer.load('nexa-model/tokenizer/production/tokenizer.json')
encoded2 = tok2.encode(text)

print('Original token count:', len(encoded1))
print('Monkey patched token count:', len(encoded2))
