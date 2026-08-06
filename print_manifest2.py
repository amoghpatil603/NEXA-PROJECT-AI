import json
with open("data/shards/pd5m_v7_8k/shard_manifest.json") as f:
    manifest = json.load(f)
print("train/doc_0.bin in manifest:", manifest.get("train/doc_0.bin"))
