import json, hashlib
from pathlib import Path

repo = Path(r"C:\Users\amogh\OneDrive\c++\project 2")
clean_dir = repo / "nexa-model" / "data" / "clean" / "pd5m_v6"

print("=" * 60)
print("STEP 1: VERIFY CERTIFIED CORPUS")
print("=" * 60)

manifest = json.load(open(repo / "data" / "acquisition" / "pd5m_v6" / "final_corpus_manifest.json"))
stats = json.load(open(repo / "data" / "acquisition" / "pd5m_v6" / "final_corpus_statistics.json"))
integrity = json.load(open(repo / "data" / "acquisition" / "pd5m_v6" / "final_artifact_integrity.json"))
security = json.load(open(repo / "data" / "reports" / "pd5m_v6_security_audit.json"))

# Verify artifact hashes
manifest_json = json.dumps(manifest, sort_keys=True)
stats_json = json.dumps(stats, sort_keys=True)
security_json = json.dumps(security, sort_keys=True)

manifest_hash = hashlib.sha256(manifest_json.encode()).hexdigest()
stats_hash = hashlib.sha256(stats_json.encode()).hexdigest()
security_hash = hashlib.sha256(security_json.encode()).hexdigest()

print(f"Manifest: {len(manifest)} works, hash={manifest_hash[:20]}...")
print(f"  Expected: {integrity['final_manifest_sha256'][:20]}...")
print(f"  Match: {manifest_hash == integrity['final_manifest_sha256']}")

print(f"Statistics: {stats['accepted_works']} works, {stats['total_clean_bytes']:,} bytes")
print(f"  Hash match: {stats_hash == integrity['final_statistics_sha256']}")

print(f"All gates pass: {stats['all_gates_pass']}")
print(f"Security: {security['result']}")
print(f"Top author: {stats['top_author']} at {stats['top_author_share_pct']}%")

# Count clean files on disk
disk_files = list(clean_dir.glob("*.txt"))
print(f"\nClean files on disk: {len(disk_files)}")

# Total clean bytes from disk
disk_bytes = sum(len(f.read_bytes()) for f in disk_files)
print(f"Clean bytes from disk: {disk_bytes:,}")
print(f"Match manifest: {disk_bytes == stats['total_clean_bytes']}")

print(f"\nCorpus VERIFIED: {all([
    manifest_hash == integrity['final_manifest_sha256'],
    stats_hash == integrity['final_statistics_sha256'],
    stats['all_gates_pass'],
    security['result'] == 'PASS',
    len(disk_files) >= 84,
    disk_bytes >= 58000000,
])}")

print("\n" + "=" * 60)
print("EXISTING TOKENIZER FILES")
print("=" * 60)

tokenizer_dir = repo / "nexa-model" / "tokenizer"
if tokenizer_dir.exists():
    for f in tokenizer_dir.iterdir():
        size = f.stat().st_size if f.is_file() else 0
        print(f"  {f.name} ({size:,} bytes)" if f.is_file() else f"  {f.name}/")
else:
    print(f"  Directory not found: {tokenizer_dir}")

tokenizers_dir = repo / "nexa-model" / "tokenizers"
if tokenizers_dir.exists():
    print(f"\ntokenizers/ contents:")
    for f in tokenizers_dir.iterdir():
        print(f"  {f.name}")

experiments_dir = repo / "tokenizers" / "experiments"
if experiments_dir.exists():
    print(f"\ntokenizers/experiments/ contents:")
    for f in experiments_dir.rglob("*"):
        if f.is_file():
            print(f"  {f.relative_to(repo)} ({f.stat().st_size:,} bytes)")

print("\n" + "=" * 60)
print("EXISTING BPE IMPLEMENTATION")
print("=" * 60)
# Look for BPE implementation
for pattern in ["**/bpe*.py", "**/tokenize*.py", "**/train_token*.py"]:
    for f in (repo / "nexa-model").rglob("*.py"):
        if "bpe" in f.name.lower() or "token" in f.name.lower():
            print(f"  {f.relative_to(repo)}")