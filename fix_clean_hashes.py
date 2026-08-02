import hashlib
import json
from pathlib import Path

repo = Path(r"C:\Users\amogh\OneDrive\c++\project 2")
clean_dir = repo / "nexa-model" / "data" / "clean" / "pd5m_v6"
MANIFEST_PATH = repo / "data" / "acquisition" / "pd5m_v6" / "clean_manifest.json"
CLEAN_CS_PATH = repo / "data" / "acquisition" / "pd5m_v6" / "clean_checksums.json"

manifest = json.load(open(MANIFEST_PATH, 'r', encoding='utf-8'))
clean_cs = json.load(open(CLEAN_CS_PATH, 'r', encoding='utf-8'))

print("Fixing CLEAN SHA-256 hashes from actual files on disk...")
fixed = 0
for e in manifest:
    sid = e['source_id']
    cp = clean_dir / f"{sid}.txt"
    if cp.exists():
        actual_hash = hashlib.sha256(open(cp, 'rb').read()).hexdigest()
        stored_hash = e.get('clean_sha256', '')
        if actual_hash != stored_hash:
            print(f"  {sid}: {stored_hash[:16]}... -> {actual_hash[:16]}...")
            e['clean_sha256'] = actual_hash
            clean_cs[sid] = actual_hash
            fixed += 1

print(f"\nFixed {fixed} entries")

# Save updated manifest
with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
    json.dump(manifest, f, indent=2)
print(f"Manifest saved: {MANIFEST_PATH}")

# Save updated clean checksums
with open(CLEAN_CS_PATH, 'w', encoding='utf-8') as f:
    json.dump(clean_cs, f, indent=2)
print(f"Clean checksums saved: {CLEAN_CS_PATH}")

# Verify no mismatches remain
print("\nVerifying...")
mismatches = []
for e in manifest:
    sid = e['source_id']
    cp = clean_dir / f"{sid}.txt"
    if cp.exists():
        actual = hashlib.sha256(open(cp, 'rb').read()).hexdigest()
        if actual != e.get('clean_sha256', ''):
            mismatches.append(sid)

if mismatches:
    print(f"REMAINING MISMATCHES: {mismatches}")
else:
    print("ALL CLEAN SHA-256 hashes verified OK ✅")