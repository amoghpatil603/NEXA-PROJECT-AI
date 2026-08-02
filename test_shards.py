from pathlib import Path
import os
import struct

def count_shards_and_tokens(split):
    dir_path = Path(f"data/shards/pd5m_v7_8k_recovered/{split}")
    shards = list(dir_path.glob("*.bin"))
    total_tokens = 0
    for shard in shards:
        size = os.path.getsize(shard)
        total_tokens += size // 4
    return len(shards), total_tokens

splits = ["train", "validation", "test"]
for s in splits:
    cnt, toks = count_shards_and_tokens(s)
    print(f"{s}: {cnt} shards, {toks} tokens")
