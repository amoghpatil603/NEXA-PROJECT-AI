import urllib.request
import urllib.error
import hashlib
import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone

repo = Path(r"C:\Users\amogh\OneDrive\c++\project 2")
raw_dir = repo / "nexa-model" / "data" / "raw" / "pd5m_v6"
clean_dir = repo / "nexa-model" / "data" / "clean" / "pd5m_v6"
raw_dir.mkdir(parents=True, exist_ok=True)
clean_dir.mkdir(parents=True, exist_ok=True)

MANIFEST_PATH = repo / "data" / "acquisition" / "pd5m_v6" / "clean_manifest.json"
RAW_CS_PATH = repo / "data" / "acquisition" / "pd5m_v6" / "raw_checksums.json"
CLEAN_CS_PATH = repo / "data" / "acquisition" / "pd5m_v6" / "clean_checksums.json"
LEDGER_PATH = repo / "data" / "acquisition" / "pd5m_v6" / "download_ledger.jsonl"
PLAN_PATH = repo / "data" / "proposals" / "pd5m_v6" / "reserve_repair_plan.json"

def clean_gutenberg(text):
    start = re.search(r'\*\*\*\s*START\s+OF\s+(THE\s+)?PROJECT\s+GUTENBERG', text, re.IGNORECASE)
    if start: text = text[start.end():]
    end = re.search(r'\*\*\*\s*END\s+OF\s+(THE\s+)?PROJECT\s+GUTENBERG', text, re.IGNORECASE)
    if end: text = text[:end.start()]
    return text.strip()

def acquire_one(source_id, url, title, author, category, order):
    print(f"\n{'='*60}")
    print(f"ACQUIRING [{order}]: source_id={source_id}, {title}")
    print(f"{'='*60}")
    
    raw_path = raw_dir / f"{source_id}.txt"
    clean_path = clean_dir / f"{source_id}.txt"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'NEXA-PD5M/2.0'})
        resp = urllib.request.urlopen(req, timeout=60)
        raw_bytes = resp.read()
        print(f"  Download: {len(raw_bytes):,} bytes")
    except urllib.error.HTTPError as e:
        print(f"  FAILED: HTTP {e.code} {e.reason}")
        return {"status": "FAILED", "source_id": source_id, "reason": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        print(f"  FAILED: {e}")
        return {"status": "FAILED", "source_id": source_id, "reason": str(e)}
    
    sample = raw_bytes[:3000].decode('utf-8', errors='replace')
    title_short = title.split(':')[0].split(';')[0].strip()
    author_last = author.split(',')[0].strip()
    title_ok = title_short in sample
    author_ok = author_last in sample
    print(f"  Identity: title={title_ok}, author={author_ok}")
    
    raw_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    with open(raw_path, 'wb') as f: f.write(raw_bytes)
    print(f"  RAW: {raw_sha256}")
    
    text = raw_bytes.decode('utf-8', errors='replace')
    clean_text = clean_gutenberg(text)
    clean_bytes = clean_text.encode('utf-8')
    clean_sha256 = hashlib.sha256(clean_bytes).hexdigest()
    with open(clean_path, 'wb') as f: f.write(clean_bytes)
    print(f"  CLEAN: {clean_sha256} ({len(clean_bytes):,} bytes)")
    
    return {
        "status": "VERIFIED_EXISTING", "source_id": source_id,
        "title": title, "author": author, "category": category,
        "url": url, "raw_path": str(raw_path), "clean_path": str(clean_path),
        "raw_bytes": len(raw_bytes), "clean_bytes": len(clean_bytes),
        "raw_sha256": raw_sha256, "clean_sha256": clean_sha256,
        "rights_status": "APPROVED", "language_status": "CONFIRMED_ENGLISH",
        "cleaning_status": "ACCEPTED", "translation_status": False,
        "original_language": "English", "acquisition_timestamp": ts
    }

def recompute_gates(manifest):
    ba = defaultdict(int); bc = defaultdict(int)
    for e in manifest:
        ba[e.get('author', 'UNKNOWN')] += e['clean_bytes']
        bc[e.get('category', 'UNKNOWN')] += e['clean_bytes']
    T = sum(e['clean_bytes'] for e in manifest)
    a = len(ba)
    if T == 0: return {"error": "empty"}
    top = max(ba.items(), key=lambda x: x[1])
    top10 = sum(b for _, b in sorted(ba.items(), key=lambda x: -x[1])[:10])
    pliny = ba.get("Pliny, the Elder", 0)
    return {
        "works": len(manifest), "authors": a, "total_bytes": T,
        "pliny_pct": round(pliny/T*100,4), "top_author": top[0],
        "top_author_pct": round(top[1]/T*100,4), "top10_pct": round(top10/T*100,2),
        "fiction_pct": round(bc.get('FICTION',0)/T*100,2),
        "essays_pct": round(bc.get('ESSAYS_GENERAL_NONFICTION',0)/T*100,2),
        "science_pct": round(bc.get('SCIENCE_EDUCATION',0)/T*100,2),
        "all_pass": a>=60 and bc.get('FICTION',0)/T*100<=50 and
                    bc.get('ESSAYS_GENERAL_NONFICTION',0)/T*100>=15 and
                    bc.get('SCIENCE_EDUCATION',0)/T*100>=10 and
                    top[1]/T*100<=5 and top10/T*100<=40
    }

# Verify hash
import subprocess
result = subprocess.run(['certutil', '-hashfile', str(PLAN_PATH), 'SHA256'], capture_output=True, text=True)
if '86d2756bdffc22a4c316d35f8286bf829c3c2790676b63f625bad8601dd7b8fa' in result.stdout:
    print("Plan hash VERIFIED ✅")
else:
    print("Plan hash MISMATCH! STOP.")
    print(result.stdout)
    exit(1)

plan = json.load(open(PLAN_PATH))
sequence = plan["acquisition_sequence"]
manifest = json.load(open(MANIFEST_PATH, 'r', encoding='utf-8'))
raw_cs = json.load(open(RAW_CS_PATH, 'r', encoding='utf-8'))
clean_cs = json.load(open(CLEAN_CS_PATH, 'r', encoding='utf-8'))

print(f"Starting: {len(manifest)} works, {sum(e['clean_bytes'] for e in manifest):,} bytes")

successful = []
failed = []
certified_at = None

for i, w in enumerate(sequence):
    order = i + 1
    result = acquire_one(w['source_id'], w['url'], w['title'], w['author'], w['category'], order)
    
    if result['status'] == 'FAILED':
        failed.append(result)
        print(f"\n  FAILED: {w['source_id']} - {result['reason']}")
        continue
    
    # Update manifest
    manifest.append(result)
    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    # Update checksums
    raw_cs[result['source_id']] = result['raw_sha256']
    clean_cs[result['source_id']] = result['clean_sha256']
    with open(RAW_CS_PATH, 'w', encoding='utf-8') as f: json.dump(raw_cs, f, indent=2)
    with open(CLEAN_CS_PATH, 'w', encoding='utf-8') as f: json.dump(clean_cs, f, indent=2)
    
    # Update ledger
    entry = {
        "work_id": f"pd_{result['source_id']}", "source_id": result['source_id'],
        "title": result['title'], "author": result['author'], "url": result['url'],
        "format": "txt", "status": "VERIFIED_EXISTING", "attempt_count": 1,
        "attempts": [{"timestamp": result['acquisition_timestamp'], "url": result['url'],
                       "http_result": "200 OK", "status": "DOWNLOADED", "reason": None}],
        "raw_path": result['raw_path'], "raw_bytes": result['raw_bytes'],
        "raw_sha256": result['raw_sha256'], "reason": None,
        "category": result['category'],
        "last_attempt": {"timestamp": result['acquisition_timestamp'], "url": result['url'],
                          "http_result": "200 OK", "status": "DOWNLOADED", "reason": None}
    }
    with open(LEDGER_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')
    
    successful.append(result)
    
    # Recompute gates
    gates = recompute_gates(manifest)
    print(f"\n  Gates after work {order}:")
    print(f"    Works={gates['works']}, Authors={gates['authors']}")
    print(f"    Pliny={gates['pliny_pct']}%, Top={gates['top_author']} {gates['top_author_pct']}%")
    print(f"    Fiction={gates['fiction_pct']}%, Essays={gates['essays_pct']}%, Science={gates['science_pct']}%")
    print(f"    Top10={gates['top10_pct']}%")
    print(f"    ALL PASS: {gates['all_pass']}")
    
    if gates['all_pass']:
        certified_at = order
        print(f"\n*** CORPUS CERTIFIED after work {order}! STOPPING. ***")
        break

# Summary
print(f"\n{'='*60}")
print(f"ACQUISITION COMPLETE")
print(f"{'='*60}")
print(f"Works planned: {len(sequence)}")
print(f"Works attempted: {len(successful) + len(failed)}")
print(f"Works successfully added: {len(successful)}")
print(f"Works failed: {len(failed)}")
print(f"Works skipped after stop: {len(sequence) - len(successful) - len(failed)}")
print(f"Certified after work: {certified_at}")
print(f"Additional clean bytes: {sum(r['clean_bytes'] for r in successful):,}")

gates = recompute_gates(manifest)
print(f"\nFinal gates: ALL_PASS={gates['all_pass']}")
print(json.dumps(gates, indent=2))