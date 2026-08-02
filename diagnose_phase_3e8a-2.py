import json
from collections import Counter, defaultdict
from pathlib import Path
import re

repo = Path(__file__).resolve().parent
acq_dir = repo / 'data' / 'acquisition' / 'pd5m_v6'
report = repo / 'data' / 'reports' / 'phase_3e8_acquisition_report.md'
ledger = acq_dir / 'download_ledger.jsonl'
clean_manifest = acq_dir / 'clean_manifest.json'
raw_checksums = acq_dir / 'raw_checksums.json'
clean_checksums = acq_dir / 'clean_checksums.json'
plan = repo / 'data' / 'proposals' / 'pd5m_v6' / 'download_plan.json'
manifest = repo / 'data' / 'proposals' / 'pd5m_v6' / 'manifest.json'
rights = repo / 'data' / 'proposals' / 'pd5m_v6' / 'rights_evidence.json'

print('report_exists', report.exists())
print('ledger_exists', ledger.exists())
print('clean_manifest_exists', clean_manifest.exists())
print('raw_checksums_exists', raw_checksums.exists())
print('clean_checksums_exists', clean_checksums.exists())

with ledger.open('r', encoding='utf-8') as f:
    ledger_records = [json.loads(line) for line in f if line.strip()]
with clean_manifest.open('r', encoding='utf-8') as f:
    clean_manifest_entries = json.load(f)
with raw_checksums.open('r', encoding='utf-8') as f:
    raw_checksums_map = json.load(f)
with clean_checksums.open('r', encoding='utf-8') as f:
    clean_checksums_map = json.load(f)
with plan.open('r', encoding='utf-8') as f:
    plan_entries = json.load(f)
with manifest.open('r', encoding='utf-8') as f:
    manifest_entries = json.load(f)
with rights.open('r', encoding='utf-8') as f:
    rights_entries = json.load(f)

plan_lookup = {entry['source_id']: entry for entry in plan_entries}
manifest_lookup = {entry['source_id']: entry for entry in manifest_entries}
rights_lookup = {entry['source_id']: entry for entry in rights_entries}

print('ledger_count', len(ledger_records))
print('clean_manifest_count', len(clean_manifest_entries))
print('raw_checksums_count', len(raw_checksums_map))
print('clean_checksums_count', len(clean_checksums_map))

print('---REPORT FIRST 40 LINES---')
with report.open('r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= 40:
            break
        print(line.rstrip())

status_counts = Counter(rec['status'] for rec in ledger_records)
print('---LEDGER STATUSES---')
for status, count in status_counts.items():
    print(status, count)

failed_records = [rec for rec in ledger_records if rec['status'] not in {'DOWNLOADED', 'VERIFIED_EXISTING'}]
print('failed_count', len(failed_records))
print('failed_source_ids', [rec['source_id'] for rec in failed_records])

accepted_sources = {entry['source_id'] for entry in clean_manifest_entries}
plan_source_ids = {entry['source_id'] for entry in plan_entries}
unsuccessful_source_ids = sorted(plan_source_ids - accepted_sources)
print('unsuccessful_count', len(unsuccessful_source_ids))
print('unsuccessful_source_ids', unsuccessful_source_ids)

WORD_PATTERN = re.compile(r"\w+", re.UNICODE)
stats = defaultdict(lambda: {'works': 0, 'clean_bytes': 0, 'characters': 0, 'words': 0, 'tokens': 0})
for entry in clean_manifest_entries:
    author = entry['author']
    clean_path = repo / 'nexa-model' / 'data' / 'clean' / 'pd5m_v6' / f"{entry['source_id']}.txt"
    text = clean_path.read_text(encoding='utf-8')
    stats[author]['works'] += 1
    stats[author]['clean_bytes'] += len(text.encode('utf-8'))
    stats[author]['characters'] += len(text)
    stats[author]['words'] += len(WORD_PATTERN.findall(text))
    stats[author]['tokens'] += len(text.encode('utf-8'))

sorted_authors = sorted(stats.items(), key=lambda kv: kv[1]['clean_bytes'], reverse=True)
print('total_clean_bytes', sum(m['clean_bytes'] for _, m in sorted_authors))
print('author_count', len(stats))
print('top15_count', min(15, len(sorted_authors)))
for rank, (author, meta) in enumerate(sorted_authors[:15], 1):
    print(rank, author, meta)

print('missing_raw_checksum', sorted([sid for sid in accepted_sources if str(sid) not in raw_checksums_map]))
print('missing_clean_checksum', sorted([sid for sid in accepted_sources if str(sid) not in clean_checksums_map]))

print('---UNSUCCESSFUL DETAILS---')
for sid in unsuccessful_source_ids:
    plan_entry = plan_lookup.get(sid, {})
    manifest_entry = manifest_lookup.get(sid, {})
    rec = next((r for r in ledger_records if r['source_id'] == sid), None)
    print('SOURCE_ID', sid)
    print(' work_id', manifest_entry.get('work_id'))
    print(' title', plan_entry.get('title'))
    print(' author', plan_entry.get('author'))
    print(' category', plan_entry.get('category'))
    print(' est_tokens', plan_entry.get('estimated_tokens') or manifest_entry.get('estimated_tokens') or plan_entry.get('token_estimate'))
    print(' url', plan_entry.get('url'))
    print(' status', rec['status'] if rec else None)
    print(' attempts', rec.get('attempt_count') if rec else None)
    print(' reason', rec.get('reason') if rec else None)
    if rec:
        for attempt in rec.get('attempts', []):
            print('  attempt', attempt.get('url'), '=>', attempt.get('http_result'), attempt.get('status'), attempt.get('reason'))
    print('---')

print('---download_integrity_formula---')
text = Path('nexa-model/scripts/acquire_pd5m_v6.py').read_text(encoding='utf-8')
for line in text.splitlines():
    if 'download_integrity' in line or 'raw_checksum_coverage' in line or 'clean_checksum_coverage' in line:
        print(line)

# Category and gate recalculation from accepted clean corpus
print('---CLEAN CORPUS GATE CALCULATION---')
category_bytes = defaultdict(int)
total_clean_bytes = 0
for entry in clean_manifest_entries:
    clean_path = repo / 'nexa-model' / 'data' / 'clean' / 'pd5m_v6' / f"{entry['source_id']}.txt"
    bytes_len = len(clean_path.read_bytes())
    category_bytes[entry['category']] += bytes_len
    total_clean_bytes += bytes_len

top_author, top_author_meta = sorted_authors[0]
top_author_share = top_author_meta['clean_bytes'] / total_clean_bytes * 100 if total_clean_bytes else 0

def pct(k):
    return category_bytes.get(k, 0) / total_clean_bytes * 100 if total_clean_bytes else 0

print('total_clean_bytes', total_clean_bytes)
print('accepted_works', len(clean_manifest_entries))
print('accepted_authors', len(sorted_authors))
print('category_shares:')
for cat in ['FICTION', 'ESSAYS_GENERAL_NONFICTION', 'SCIENCE_EDUCATION', 'HISTORY_BIOGRAPHY', 'PHILOSOPHY_SOCIAL_THOUGHT']:
    print(f'  {cat}: {pct(cat):.1f}%')
other_share = sum(v for k,v in category_bytes.items() if k not in {'FICTION', 'ESSAYS_GENERAL_NONFICTION', 'SCIENCE_EDUCATION', 'HISTORY_BIOGRAPHY', 'PHILOSOPHY_SOCIAL_THOUGHT'})
print(f'  OTHER: {other_share / total_clean_bytes * 100:.1f}%')
print('top_author', top_author)
print('top_author_works', top_author_meta['works'])
print('top_author_clean_bytes', top_author_meta['clean_bytes'])
print('top_author_share', top_author_share)
print('top10_share', sum(m['clean_bytes'] for _,m in sorted_authors[:10]) / total_clean_bytes * 100)
print('required_total_for_5pct', top_author_meta['clean_bytes'] / 0.05)
print('additional_clean_bytes_needed', top_author_meta['clean_bytes'] / 0.05 - total_clean_bytes)

print('---RESERVE METADATA---')
reserve = json.load((repo/'data'/'proposals'/'pd5m_v6'/'reserve.json').open('r',encoding='utf-8'))
print('reserve_count', len(reserve))
reserve_authors = Counter(e['author'] for e in reserve)
print('reserve_top_authors', reserve_authors.most_common(10))
print('reserve_categories', Counter(e['category'] for e in reserve))
print('reserve_estimated_tokens', Counter(e['estimated_tokens'] for e in reserve))
print('reserve_sample')
for entry in reserve[:10]:
    print(' ', entry['work_id'], entry['source_id'], entry['author'], entry['category'], entry['estimated_tokens'])
