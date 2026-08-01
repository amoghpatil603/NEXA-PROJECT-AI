import json
from pathlib import Path
shard_dir = Path("data/shards/pd5m_v7_8k")
for split in ["train", "validation", "test"]:
    shards = list((shard_dir / split).glob("*.bin"))
    total = sum(shard.stat().st_size // 2 for shard in shards)
    print(f"{split} docs: {len(shards)}, tokens: {total}")
