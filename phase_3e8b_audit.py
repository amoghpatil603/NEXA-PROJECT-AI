import json
from pathlib import Path
from collections import Counter, defaultdict
import re

repo = Path(__file__).resolve().parent
acq_dir = repo / 'data' / 'acquisition' / 'pd5m_v6'
clean_manifest_file = acq_dir / 'clean_manifest.json'
raw_checksums_file = acq_dir / 'raw_checksums.json'
clean_checksums_file = acq_dir / 'clean_checksums.json'
ledger_file = acq_dir / 'download_ledger.jsonl'
audit_file = repo / 'data' / 'reports' / 'phase_3e8b_pre_repair_audit.json'

with ledger_file.open('r', encoding='utf-8') as f:
    ledger = [json.loads(line) for line in f if line.strip()]
with clean_manifest_file.open('r', encoding='utf-8') as f:
    clean_manifest = json.load(f)
with raw_checksums_file.open('r', encoding='utf-8') as f:
    raw_checksums = json.load(f)
with clean_checksums_file.open('r', encoding='utf-8') as f:
    clean_checksums = json.load(f)

accepted_work_count = len(clean_manifest)
unique_authors = len(set(entry['author'] for entry in clean_manifest))
raw_checksum_coverage = len(raw_checksums)
clean_checksum_coverage = len(clean_checksums)

clean_bytes_by_file = {}
char_count = 0
word_count = 0
byte_tokenizer_tokens = 0
WORD_PATTERN = re.compile(r"\w+", re.UNICODE)
category_bytes = defaultdict(int)
source_ids = []
for entry in clean_manifest:
    source_id = str(entry['source_id'])
    source_ids.append(source_id)
    clean_path = repo / 'nexa-model' / 'data' / 'clean' / 'pd5m_v6' / f"{source_id}.txt"
    raw_data = clean_path.read_bytes()
    clean_bytes_by_file[source_id] = len(raw_data)
    text = raw_data.decode('utf-8')
    char_count += len(text)
    word_count += len(WORD_PATTERN.findall(text))
    byte_tokenizer_tokens += len(raw_data)
    category_bytes[entry['category']] += len(raw_data)

clean_bytes = sum(clean_bytes_by_file.values())

# determine top author shares
author_stats = defaultdict(lambda: {'works': 0, 'clean_bytes': 0, 'characters': 0, 'words': 0})
for entry in clean_manifest:
    source_id = str(entry['source_id'])
    author = entry['author']
    author_stats[author]['works'] += 1
    author_stats[author]['clean_bytes'] += clean_bytes_by_file[source_id]
    clean_path = repo / 'nexa-model' / 'data' / 'clean' / 'pd5m_v6' / f"{source_id}.txt"
    text = clean_path.read_text(encoding='utf-8')
    author_stats[author]['characters'] += len(text)
    author_stats[author]['words'] += len(WORD_PATTERN.findall(text))

sorted_authors = sorted(author_stats.items(), key=lambda kv: kv[1]['clean_bytes'], reverse=True)
if sorted_authors:
    top_author = sorted_authors[0][0]
    top_author_bytes = sorted_authors[0][1]['clean_bytes']
    top_author_share = top_author_bytes / clean_bytes * 100 if clean_bytes else 0
    top10_share = sum(m['clean_bytes'] for _, m in sorted_authors[:10]) / clean_bytes * 100 if clean_bytes else 0
else:
    top_author = None
    top_author_share = 0
    top10_share = 0

# compare manifest declared clean bytes vs actual files
manifest_declared_clean_bytes = sum(entry['clean_bytes'] for entry in clean_manifest if isinstance(entry.get('clean_bytes'), int))
manifest_file_discrepancies = [
    {
        'source_id': str(entry['source_id']),
        'declared_clean_bytes': entry.get('clean_bytes'),
        'actual_clean_bytes': clean_bytes_by_file.get(str(entry['source_id']))
    }
    for entry in clean_manifest
    if entry.get('clean_bytes') != clean_bytes_by_file.get(str(entry['source_id']))
]

# raw accepted count from ledger
accepted_raw_count = sum(1 for rec in ledger if rec['status'] in {'DOWNLOADED', 'VERIFIED_EXISTING'})

# create audit
audit = {
    'accepted_work_count': accepted_work_count,
    'unique_author_count': unique_authors,
    'clean_byte_count': clean_bytes,
    'accepted_raw_count': accepted_raw_count,
    'raw_checksum_coverage': raw_checksum_coverage,
    'clean_checksum_coverage': clean_checksum_coverage,
    'category_distribution': {k: v / clean_bytes * 100 for k, v in category_bytes.items()},
    'top_author': top_author,
    'top_author_clean_bytes': top_author_bytes,
    'top_author_share_pct': top_author_share,
    'top10_share_pct': top10_share,
    'manifest_declared_clean_bytes': manifest_declared_clean_bytes,
    'manifest_actual_clean_bytes': clean_bytes,
    'manifest_clean_bytes_discrepancies': manifest_file_discrepancies,
    'accepted_raw_count_matches_raw_checksum_coverage': accepted_raw_count == raw_checksum_coverage,
    'accepted_clean_count_matches_clean_checksum_coverage': accepted_work_count == clean_checksum_coverage,
}

audit_file.parent.mkdir(parents=True, exist_ok=True)
audit_file.write_text(json.dumps(audit, indent=2), encoding='utf-8')
print('Wrote audit to', audit_file)
print(json.dumps(audit, indent=2))
