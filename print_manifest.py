import json
with open("data/shards/pd5m_v7_8k/shard_manifest.json") as f:
    manifest = json.load(f)
for split in ["train", "validation", "test"]:
    count = sum(info["token_count"] for info in manifest.values() if info["split"] == split)
    print(f"{split}: {count}")
