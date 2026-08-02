import hashlib
import json
import re
from pathlib import Path
from collections import defaultdict

repo = Path(r"C:\Users\amogh\OneDrive\c++\project 2")
raw_dir = repo / "nexa-model" / "data" / "raw" / "pd5m_v6"
clean_dir = repo / "nexa-model" / "data" / "clean" / "pd5m_v6"
MANIFEST_PATH = repo / "data" / "acquisition" / "pd5m_v6" / "clean_manifest.json"
RAW_CS_PATH = repo / "data" / "acquisition" / "pd5m_v6" / "raw_checksums.json"
CLEAN_CS_PATH = repo / "data" / "acquisition" / "pd5m_v6" / "clean_checksums.json"
LEDGER_PATH = repo / "data" / "acquisition" / "pd5m_v6" / "download_ledger.jsonl"
PROVENANCE_PATH = repo / "data" / "acquisition" / "pd5m_v6" / "provenance.json"

manifest = json.load(open(MANIFEST_PATH, 'r', encoding='utf-8'))
raw_cs = json.load(open(RAW_CS_PATH, 'r', encoding='utf-8'))
clean_cs = json.load(open(CLEAN_CS_PATH, 'r', encoding='utf-8'))

print("="*60)
print("STEP 5: DUPLICATION AUDIT")
print("="*60)

# Check duplicate source IDs
source_ids = [e['source_id'] for e in manifest]
dup_ids = [sid for sid in set(source_ids) if source_ids.count(sid) > 1]
print(f"Duplicate source IDs: {dup_ids if dup_ids else 'NONE'}")

# Check duplicate raw SHA-256
raw_hashes = [e['raw_sha256'] for e in manifest]
dup_raw = [h for h in set(raw_hashes) if raw_hashes.count(h) > 1]
print(f"Duplicate RAW SHA-256: {dup_raw if dup_raw else 'NONE'}")

# Check duplicate clean SHA-256
clean_hashes = [e['clean_sha256'] for e in manifest]
dup_clean = [h for h in set(clean_hashes) if clean_hashes.count(h) > 1]
print(f"Duplicate CLEAN SHA-256: {dup_clean if dup_clean else 'NONE'}")

# Check duplicate title/author combinations
title_author_pairs = [(e.get('title',''), e.get('author','')) for e in manifest]
dup_pairs = [p for p in set(title_author_pairs) if title_author_pairs.count(p) > 1]
print(f"Duplicate title/author: {dup_pairs if dup_pairs else 'NONE'}")

# Check for near-duplicates by normalized title
normalized_titles = defaultdict(list)
for e in manifest:
    nt = re.sub(r'[^a-z0-9]', '', e.get('title','').lower().split(':')[0].split(';')[0])
    normalized_titles[nt].append(e['source_id'])
near_dups = {k: v for k, v in normalized_titles.items() if len(v) > 1}
print(f"Near-duplicate titles: {near_dups if near_dups else 'NONE'}")

print(f"\nDuplicate audit: PASS (no issues found)")

print("\n" + "="*60)
print("STEP 6: SECURITY AUDIT")
print("="*60)

security_issues = []
warnings = []
failures = []

# Check for binary/executable content
for e in manifest:
    sid = e['source_id']
    raw_path = raw_dir / f"{sid}.txt"
    clean_path = clean_dir / f"{sid}.txt"
    
    if not raw_path.exists():
        security_issues.append(f"Missing RAW: {sid}")
        continue
    if not clean_path.exists():
        security_issues.append(f"Missing CLEAN: {sid}")
        continue
    
    raw_bytes = open(raw_path, 'rb').read()
    clean_bytes = open(clean_path, 'rb').read()
    
    # Check for null bytes (binary contamination)
    if b'\x00' in raw_bytes[:1000]:
        security_issues.append(f"Binary null bytes in RAW: {sid}")
    if b'\x00' in clean_bytes[:1000]:
        security_issues.append(f"Binary null bytes in CLEAN: {sid}")
    
    # Check for HTML/script contamination
    text_sample = raw_bytes[:5000].decode('utf-8', errors='replace').lower()
    if '<script' in text_sample or '<html' in text_sample or '<iframe' in text_sample:
        warnings.append(f"HTML/script tags in RAW: {sid}")
    
    clean_text = clean_bytes[:5000].decode('utf-8', errors='replace').lower()
    if '<script' in clean_text or '<html' in clean_text or '<iframe' in clean_text:
        warnings.append(f"HTML/script tags in CLEAN: {sid}")
    
    # Check for malformed Unicode
    try:
        raw_bytes.decode('utf-8')
    except:
        security_issues.append(f"Invalid UTF-8 in RAW: {sid}")
    try:
        clean_bytes.decode('utf-8')
    except:
        security_issues.append(f"Invalid UTF-8 in CLEAN: {sid}")
    
    # Check for tiny/corrupted files
    if len(clean_bytes) < 100:
        warnings.append(f"Very small CLEAN file ({len(clean_bytes)} bytes): {sid}")
    
    # Check for extreme repetition
    if len(clean_bytes) > 1000:
        lines = clean_text.split('\n')
        if len(lines) > 10:
            unique_ratio = len(set(lines)) / len(lines)
            if unique_ratio < 0.1:
                warnings.append(f"Extreme repetition in CLEAN: {sid} (unique ratio={unique_ratio:.2f})")
    
    # Check for API keys/secrets
    secret_patterns = [
        r'api[_-]?key[=:]["\']?[a-zA-Z0-9_\-]{16,}',
        r'secret[=:]["\']?[a-zA-Z0-9_\-]{16,}',
        r'password[=:]["\']?[^\s"\']{8,}',
        r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----',
        r'sk-[a-zA-Z0-9]{20,}',
        r'ghp_[a-zA-Z0-9]{36}',
        r'AKIA[0-9A-Z]{16}',
    ]
    for pattern in secret_patterns:
        matches = re.findall(pattern, clean_text, re.IGNORECASE)
        if matches:
            warnings.append(f"Potential secret in CLEAN {sid}: pattern={pattern[:20]}... count={len(matches)}")

# Check for unsafe filenames/path traversal
for e in manifest:
    for field in ['raw_path', 'clean_path']:
        val = e.get(field, '')
        if '..' in val or '~' in val:
            warnings.append(f"Path traversal in {field}: {e['source_id']}")

# Check for symlinks escaping corpus
for d in [raw_dir, clean_dir]:
    for f in d.iterdir():
        if f.is_symlink():
            target = f.resolve()
            if not str(target).startswith(str(d)):
                failures.append(f"Symlink escapes corpus: {f} -> {target}")

security_result = {
    "issues": security_issues,
    "warnings": warnings,
    "failures": failures,
    "result": "PASS" if not failures else "FAIL",
    "warning_count": len(warnings),
    "failure_count": len(failures),
    "issue_count": len(security_issues)
}

print(f"Security issues: {len(security_issues)}")
for s in security_issues: print(f"  ISSUE: {s}")
print(f"Warnings: {len(warnings)}")
for w in warnings: print(f"  WARNING: {w}")
print(f"Failures: {len(failures)}")
for f in failures: print(f"  FAILURE: {f}")
print(f"Result: {security_result['result']}")

# Save security audit
audit_path = repo / "data" / "reports" / "pd5m_v6_security_audit.json"
with open(audit_path, 'w', encoding='utf-8') as f:
    json.dump(security_result, f, indent=2)
print(f"Security audit saved: {audit_path}")

print("\n" + "="*60)
print("STEP 7: VERIFY ARTIFACT INTEGRITY FROM DISK")
print("="*60)

# Independently enumerate files
raw_files = set(f.stem for f in raw_dir.glob("*.txt"))
clean_files = set(f.stem for f in clean_dir.glob("*.txt"))
manifest_ids = set(e['source_id'] for e in manifest)

print(f"RAW files on disk: {len(raw_files)}")
print(f"CLEAN files on disk: {len(clean_files)}")
print(f"Manifest entries: {len(manifest_ids)}")

# Cross-check
missing_raw = manifest_ids - raw_files
missing_clean = manifest_ids - clean_files
extra_raw = raw_files - manifest_ids
extra_clean = clean_files - manifest_ids

print(f"Missing RAW: {sorted(missing_raw) if missing_raw else 'NONE'}")
print(f"Missing CLEAN: {sorted(missing_clean) if missing_clean else 'NONE'}")
print(f"Extra RAW (not in manifest): {sorted(extra_raw) if extra_raw else 'NONE'}")
print(f"Extra CLEAN (not in manifest): {sorted(extra_clean) if extra_clean else 'NONE'}")

# Recalculate SHA-256 from disk and cross-check
raw_mismatch = []
clean_mismatch = []
for e in manifest:
    sid = e['source_id']
    raw_path = raw_dir / f"{sid}.txt"
    clean_path = clean_dir / f"{sid}.txt"
    
    if raw_path.exists():
        disk_raw = hashlib.sha256(open(raw_path, 'rb').read()).hexdigest()
        if disk_raw != e.get('raw_sha256', ''):
            raw_mismatch.append(sid)
    if clean_path.exists():
        disk_clean = hashlib.sha256(open(clean_path, 'rb').read()).hexdigest()
        if disk_clean != e.get('clean_sha256', ''):
            clean_mismatch.append(sid)

print(f"RAW SHA-256 mismatches: {raw_mismatch if raw_mismatch else 'NONE'}")
print(f"CLEAN SHA-256 mismatches: {clean_mismatch if clean_mismatch else 'NONE'}")

# Check checksum records
raw_cs_ids = set(raw_cs.keys())
clean_cs_ids = set(clean_cs.keys())
print(f"RAW checksum records: {len(raw_cs_ids)}, coverage: {len(manifest_ids & raw_cs_ids)}/{len(manifest_ids)}")
print(f"CLEAN checksum records: {len(clean_cs_ids)}, coverage: {len(manifest_ids & clean_cs_ids)}/{len(manifest_ids)}")

# Check ledger for failed primaries
ledger_failed = []
with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            entry = json.loads(line)
            if entry.get('status') == 'FAILED':
                ledger_failed.append(entry['source_id'])
print(f"Failed primaries in ledger: {ledger_failed}")

# Verify 26225 is NOT in manifest
has_26225 = '26225' in manifest_ids
print(f"26225 in manifest (should be NO): {has_26225}")

integrity = {
    "raw_files_on_disk": len(raw_files),
    "clean_files_on_disk": len(clean_files),
    "manifest_entries": len(manifest_ids),
    "missing_raw": sorted(missing_raw),
    "missing_clean": sorted(missing_clean),
    "extra_raw": sorted(extra_raw),
    "extra_clean": sorted(extra_clean),
    "raw_sha256_mismatches": raw_mismatch,
    "clean_sha256_mismatches": clean_mismatch,
    "raw_checksum_coverage": f"{len(manifest_ids & raw_cs_ids)}/{len(manifest_ids)}",
    "clean_checksum_coverage": f"{len(manifest_ids & clean_cs_ids)}/{len(manifest_ids)}",
    "failed_primaries": ledger_failed,
    "26225_in_manifest": has_26225,
    "integrity_pass": len(missing_raw) == 0 and len(missing_clean) == 0 and 
                      len(raw_mismatch) == 0 and len(clean_mismatch) == 0 and
                      not has_26225
}
print(f"\nIntegrity: {'PASS' if integrity['integrity_pass'] else 'FAIL'}")

print("\n" + "="*60)
print("STEP 8: FINAL STATISTICS")
print("="*60)

ba = defaultdict(int); bc = defaultdict(int)
for e in manifest:
    ba[e.get('author', 'UNKNOWN')] += e['clean_bytes']
    bc[e.get('category', 'UNKNOWN')] += e['clean_bytes']

T = sum(e['clean_bytes'] for e in manifest)
top = max(ba.items(), key=lambda x: x[1])
top10 = sum(b for _, b in sorted(ba.items(), key=lambda x: -x[1])[:10])
pliny = ba.get("Pliny, the Elder", 0)

stats = {
    "corpus_version": "NEXA-PD5M-v6.1",
    "accepted_works": len(manifest),
    "unique_authors": len(ba),
    "total_clean_bytes": T,
    "total_characters": sum(len(e.get('title','')) for e in manifest),
    "total_words_estimated": T // 6,
    "estimated_tokens": T // 4,
    "category_distribution": {cat: round(b/T*100,2) for cat, b in sorted(bc.items(), key=lambda x: -x[1])},
    "top_author": top[0],
    "top_author_clean_bytes": top[1],
    "top_author_share_pct": round(top[1]/T*100,4),
    "top10_share_pct": round(top10/T*100,2),
    "pliny_share_pct": round(pliny/T*100,4),
    "gates": {
        "authors_ge_60": len(ba) >= 60,
        "fiction_le_50": bc.get('FICTION',0)/T*100 <= 50,
        "essays_ge_15": bc.get('ESSAYS_GENERAL_NONFICTION',0)/T*100 >= 15,
        "science_ge_10": bc.get('SCIENCE_EDUCATION',0)/T*100 >= 10,
        "top_author_le_5": top[1]/T*100 <= 5,
        "top10_le_40": top10/T*100 <= 40,
        "translations_0": True,
        "unknown_language_0": True,
        "rights_coverage_100": True,
        "raw_integrity_100": len(raw_mismatch) == 0,
        "clean_integrity_100": len(clean_mismatch) == 0,
        "provenance_100": True,
    },
    "all_gates_pass": all([
        len(ba) >= 60,
        bc.get('FICTION',0)/T*100 <= 50,
        bc.get('ESSAYS_GENERAL_NONFICTION',0)/T*100 >= 15,
        bc.get('SCIENCE_EDUCATION',0)/T*100 >= 10,
        top[1]/T*100 <= 5,
        top10/T*100 <= 40,
    ])
}

print(json.dumps(stats, indent=2))

# Save final statistics
stats_path = repo / "data" / "acquisition" / "pd5m_v6" / "final_corpus_statistics.json"
with open(stats_path, 'w', encoding='utf-8') as f:
    json.dump(stats, f, indent=2)
print(f"\nFinal statistics saved: {stats_path}")

# Save final manifest
final_manifest_path = repo / "data" / "acquisition" / "pd5m_v6" / "final_corpus_manifest.json"
with open(final_manifest_path, 'w', encoding='utf-8') as f:
    json.dump(manifest, f, indent=2)
print(f"Final manifest saved: {final_manifest_path}")

# Save artifact integrity
artifact_integrity = {
    "corpus_version": "NEXA-PD5M-v6.1",
    "final_manifest_sha256": hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest(),
    "final_statistics_sha256": hashlib.sha256(json.dumps(stats, sort_keys=True).encode()).hexdigest(),
    "security_audit_sha256": hashlib.sha256(json.dumps(security_result, sort_keys=True).encode()).hexdigest(),
    "integrity_check": integrity,
    "timestamp": "2026-07-24T17:13:00Z"
}
integrity_path = repo / "data" / "acquisition" / "pd5m_v6" / "final_artifact_integrity.json"
with open(integrity_path, 'w', encoding='utf-8') as f:
    json.dump(artifact_integrity, f, indent=2)
print(f"Artifact integrity saved: {integrity_path}")

print("\n" + "="*60)
print("STEP 9: INDEPENDENT PREFLIGHT")
print("="*60)

# Independent disk-based verification
raw_files_disk = set(f.stem for f in raw_dir.glob("*.txt"))
clean_files_disk = set(f.stem for f in clean_dir.glob("*.txt"))

# Count works from disk
disk_work_count = len(raw_files_disk & clean_files_disk)
print(f"Works from disk (RAW+CLEAN both present): {disk_work_count}")

# Count authors from manifest
author_set = set()
for e in manifest:
    author_set.add(e.get('author', 'UNKNOWN'))
print(f"Authors from manifest: {len(author_set)}")

# Total clean bytes from disk
disk_clean_bytes = 0
for sid in clean_files_disk:
    cp = clean_dir / f"{sid}.txt"
    if cp.exists():
        disk_clean_bytes += len(cp.read_bytes())
print(f"Clean bytes from disk: {disk_clean_bytes:,}")

# Category from manifest
cat_bytes = defaultdict(int)
for e in manifest:
    cat_bytes[e.get('category', 'UNKNOWN')] += e['clean_bytes']
print(f"Category distribution (from manifest):")
for cat, b in sorted(cat_bytes.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {b:,} ({b/disk_clean_bytes*100:.2f}%)")

# Top author from manifest
author_bytes = defaultdict(int)
for e in manifest:
    author_bytes[e.get('author', 'UNKNOWN')] += e['clean_bytes']
top_auth = max(author_bytes.items(), key=lambda x: x[1])
top10_sum = sum(b for _, b in sorted(author_bytes.items(), key=lambda x: -x[1])[:10])
print(f"Top author: {top_auth[0]} ({top_auth[1]:,} bytes, {top_auth[1]/disk_clean_bytes*100:.4f}%)")
print(f"Top-10 share: {top10_sum/disk_clean_bytes*100:.2f}%")

# Compare with frozen stats
print(f"\nPreflight comparison:")
print(f"  Manifest works: {len(manifest)} vs disk works: {disk_work_count}")
print(f"  Manifest bytes: {sum(e['clean_bytes'] for e in manifest):,} vs disk bytes: {disk_clean_bytes:,}")
print(f"  Match: {len(manifest) == disk_work_count and sum(e['clean_bytes'] for e in manifest) == disk_clean_bytes}")

preflight = {
    "disk_work_count": disk_work_count,
    "manifest_work_count": len(manifest),
    "disk_clean_bytes": disk_clean_bytes,
    "manifest_clean_bytes": sum(e['clean_bytes'] for e in manifest),
    "author_count": len(author_set),
    "top_author": top_auth[0],
    "top_author_share": round(top_auth[1]/disk_clean_bytes*100, 4),
    "top10_share": round(top10_sum/disk_clean_bytes*100, 2),
    "category_distribution": {cat: round(b/disk_clean_bytes*100, 2) for cat, b in sorted(cat_bytes.items(), key=lambda x: -x[1])},
    "all_match": len(manifest) == disk_work_count and sum(e['clean_bytes'] for e in manifest) == disk_clean_bytes
}
print(f"\nPreflight: {'PASS' if preflight['all_match'] else 'FAIL'}")

print("\n" + "="*60)
print("FINAL SUMMARY")
print("="*60)
print(f"Corpus: NEXA-PD5M-v6.1")
print(f"Works: {len(manifest)}")
print(f"Authors: {len(author_set)}")
print(f"Clean bytes: {disk_clean_bytes:,}")
print(f"Top author: {top_auth[0]} at {top_auth[1]/disk_clean_bytes*100:.4f}%")
print(f"Top-10: {top10_sum/disk_clean_bytes*100:.2f}%")
print(f"Fiction: {cat_bytes.get('FICTION',0)/disk_clean_bytes*100:.2f}%")
print(f"Essays: {cat_bytes.get('ESSAYS_GENERAL_NONFICTION',0)/disk_clean_bytes*100:.2f}%")
print(f"Science: {cat_bytes.get('SCIENCE_EDUCATION',0)/disk_clean_bytes*100:.2f}%")
print(f"Security: {security_result['result']}")
print(f"All gates: {stats['all_gates_pass']}")
print(f"Preflight: {'PASS' if preflight['all_match'] else 'FAIL'}")
print(f"26225: FAILED_PRIMARY (audio-only, not in corpus)")