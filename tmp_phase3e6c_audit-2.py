import hashlib
import json
import os
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

root = Path(os.getcwd())
manifest_path = root / 'data' / 'proposals' / 'pd5m_v6' / 'manifest.json'
reserve_path = root / 'data' / 'proposals' / 'pd5m_v6' / 'reserve.json'
evidence_path = root / 'data' / 'catalog' / 'work_language_evidence.json'

manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
reserve = json.loads(reserve_path.read_text(encoding='utf-8'))
evidence = json.loads(evidence_path.read_text(encoding='utf-8'))

# compute manifest hash
raw = manifest_path.read_bytes()
manifest_hash = hashlib.sha256(raw).hexdigest()
run_id = f'pd5m_v6_{datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")}_{manifest_hash[:12]}'

print('manifest_count', len(manifest))
print('reserve_count', len(reserve))
print('manifest_hash', manifest_hash)
print('run_id', run_id)
print('manifest_sample_keys', list(manifest[0].keys()))
print('reserve_sample_keys', list(reserve[0].keys()))
print('evidence_keys_sample', list(evidence.get('works', {}).get(manifest[0].get('work_id', ''), {}).keys()))
print('manifest0', {k: manifest[0].get(k) for k in ['work_id', 'source_id', 'title', 'author', 'language_status', 'language_evidence', 'rights_evidence', 'publication_year']})
print('reserve0', {k: reserve[0].get(k) for k in ['work_id', 'source_id', 'title', 'author', 'language_status', 'language_evidence', 'rights_evidence', 'publication_year']})

# evidence gate fields from manifest
for w in manifest[:5]:
    missing = [f for f in ['language_status', 'language_evidence', 'rights_evidence'] if not w.get(f)]
    if missing:
        print('missing_fields', w.get('work_id'), missing)

# inspect sample evidence entry
if manifest:
    first_id = manifest[0].get('work_id')
    print('evidence_entry', first_id, evidence.get('works', {}).get(first_id))
