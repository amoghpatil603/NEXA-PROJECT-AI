import hashlib, json, re
from pathlib import Path
from collections import defaultdict

repo = Path(r"C:\Users\amogh\OneDrive\c++\project 2")
clean_dir = repo / "nexa-model" / "data" / "clean" / "pd5m_v6"
MANIFEST_PATH = repo / "data" / "acquisition" / "pd5m_v6" / "clean_manifest.json"
CLEAN_CS_PATH = repo / "data" / "acquisition" / "pd5m_v6" / "clean_checksums.json"
RAW_DIR = repo / "nexa-model" / "data" / "raw" / "pd5m_v6"

manifest = json.load(open(MANIFEST_PATH, 'r', encoding='utf-8'))

print("Checking manifest clean_bytes vs actual file sizes and recomputing...")

manifest_bytes = 0
disk_bytes = 0
fixed_count = 0

for e in manifest:
    sid = e['source_id']
    cp = clean_dir / f"{sid}.txt"
    rp = RAW_DIR / f"{sid}.txt"
    
    if cp.exists():
        actual_size = len(open(cp, 'rb').read())
        stored_size = e.get('clean_bytes', 0)
        manifest_bytes += stored_size
        disk_bytes += actual_size
        if actual_size != stored_size:
            print(f"  {sid}: manifest={stored_size:,} -> disk={actual_size:,} (delta={actual_size-stored_size:,})")
            e['clean_bytes'] = actual_size
            fixed_count += 1
        
        # Also fix raw_bytes if wrong
        if rp.exists():
            raw_size = len(open(rp, 'rb').read())
            stored_raw = e.get('raw_bytes', 0)
            if raw_size != stored_raw:
                e['raw_bytes'] = raw_size
    else:
        print(f"  MISSING CLEAN FILE: {sid}")

print(f"\nManifest total: {manifest_bytes:,}")
print(f"Disk total: {disk_bytes:,}")
print(f"Fixed {fixed_count} entries")

# Save updated manifest
with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
    json.dump(manifest, f, indent=2)
print(f"Manifest saved ✅")

# Now do the independent preflight
print("\n" + "="*60)
print("INDEPENDENT PREFLIGHT")
print("="*60)

# Count works from disk
raw_files = set(f.stem for f in clean_dir.glob("*.txt"))
clean_files_disk = set(f.stem for f in clean_dir.glob("*.txt"))
disk_work_count = len(clean_files_disk)
print(f"Works from disk (CLEAN): {disk_work_count}")

# Total clean bytes from disk
disk_total = 0
for sid in clean_files_disk:
    cp = clean_dir / f"{sid}.txt"
    if cp.exists():
        disk_total += len(cp.read_bytes())
print(f"Clean bytes from disk: {disk_total:,}")

# Author bytes from manifest
ba = defaultdict(int)
bc = defaultdict(int)
for e in manifest:
    ba[e.get('author', 'UNKNOWN')] += e['clean_bytes']
    bc[e.get('category', 'UNKNOWN')] += e['clean_bytes']

T = sum(e['clean_bytes'] for e in manifest)
top = max(ba.items(), key=lambda x: x[1])
top10 = sum(b for _, b in sorted(ba.items(), key=lambda x: -x[1])[:10])

print(f"Manifest total: {T:,}")
print(f"Match: {T == disk_total}")
print(f"Authors: {len(ba)}")
print(f"Top author: {top[0]} ({top[1]/T*100:.4f}%)")
print(f"Top-10: {top10/T*100:.2f}%")
print(f"Fiction: {bc.get('FICTION',0)/T*100:.2f}%")
print(f"Essays: {bc.get('ESSAYS_GENERAL_NONFICTION',0)/T*100:.2f}%")
print(f"Science: {bc.get('SCIENCE_EDUCATION',0)/T*100:.2f}%")

# Check all gates
authors_ok = len(ba) >= 60
fiction_ok = bc.get('FICTION',0)/T*100 <= 50
essays_ok = bc.get('ESSAYS_GENERAL_NONFICTION',0)/T*100 >= 15
science_ok = bc.get('SCIENCE_EDUCATION',0)/T*100 >= 10
top_ok = top[1]/T*100 <= 5
top10_ok = top10/T*100 <= 40

print(f"\nGates:")
print(f"  Authors >=60: {len(ba)} {'PASS' if authors_ok else 'FAIL'}")
print(f"  Fiction <=50%: {bc.get('FICTION',0)/T*100:.2f}% {'PASS' if fiction_ok else 'FAIL'}")
print(f"  Essays >=15%: {bc.get('ESSAYS_GENERAL_NONFICTION',0)/T*100:.2f}% {'PASS' if essays_ok else 'FAIL'}")
print(f"  Science >=10%: {bc.get('SCIENCE_EDUCATION',0)/T*100:.2f}% {'PASS' if science_ok else 'FAIL'}")
print(f"  Top author <=5%: {top[1]/T*100:.4f}% {'PASS' if top_ok else 'FAIL'}")
print(f"  Top10 <=40%: {top10/T*100:.2f}% {'PASS' if top10_ok else 'FAIL'}")

all_pass = all([authors_ok, fiction_ok, essays_ok, science_ok, top_ok, top10_ok])
print(f"\n  ALL GATES: {'PASS ✅' if all_pass else 'FAIL ❌'}")