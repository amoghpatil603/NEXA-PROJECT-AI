import json, hashlib
from pathlib import Path

def sha256_file(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()

checksum_path = Path("data/shards/pd5m_v7_8k/checksums.json")
with open(checksum_path, "r") as f:
    checksums = json.load(f)

for rel_path, expected_hash in checksums.items():
    file_path = Path("data/shards/pd5m_v7_8k") / rel_path
    actual_hash = sha256_file(file_path)
    if actual_hash != expected_hash:
        print(f"Hash mismatch for {rel_path}: Expected {expected_hash}, got {actual_hash}")
        break
else:
    print("All hashes match!")
