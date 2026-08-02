import json
import hashlib
import pathlib
import shutil
import tempfile
import subprocess
from collections import Counter

root = pathlib.Path.cwd()
proposal_root = root / 'data' / 'proposals' / 'pd5m_v6'
required_files = [
    'manifest.json',
    'statistics.json',
    'rights_evidence.json',
    'selection_log.json',
    'review.md',
    'reserve.json',
    'download_plan.json',
    'artifact_integrity.json',
    'phase3e7_preflight_report.json',
]

print('=== FILE EXISTENCE ===')
exists = {f: (proposal_root / f).exists() for f in required_files}
for f, ok in exists.items():
    print(f, ok)

print('\n=== HASH CHECKS ===')
integrity = json.load((proposal_root / 'artifact_integrity.json').open('r', encoding='utf-8'))
print('algorithm', integrity.get('algorithm'))
hash_mismatches = []
for name, expected in integrity.get('files', {}).items():
    p = proposal_root / name
    actual = hashlib.sha256(p.read_bytes()).hexdigest()
    ok = actual == expected
    print(name, ok)
    if not ok:
        hash_mismatches.append((name, expected, actual))
print('hash_mismatch_count', len(hash_mismatches))
for item in hash_mismatches:
    print('mismatch', item)

print('\n=== MANIFEST / STATISTICS CONSISTENCY ===')
manifest = json.load((proposal_root / 'manifest.json').open('r', encoding='utf-8'))
stats = json.load((proposal_root / 'statistics.json').open('r', encoding='utf-8'))
reserve = json.load((proposal_root / 'reserve.json').open('r', encoding='utf-8'))
download = json.load((proposal_root / 'download_plan.json').open('r', encoding='utf-8'))
rights = json.load((proposal_root / 'rights_evidence.json').open('r', encoding='utf-8'))
evidence = json.load((root / 'data' / 'catalog' / 'work_language_evidence.json').open('r', encoding='utf-8'))

print('manifest_entries', len(manifest))
print('stats_selected_works', stats.get('selected_works'))
print('stats_authors', stats.get('selected_authors'))
print('stats_tokens', stats.get('selected_tokens'))
print('reserve_works', len(reserve))
print('reserve_authors', len(set(r['author'] for r in reserve)))
print('reserve_tokens', sum(r.get('estimated_tokens', 0) for r in reserve))

cats = Counter()
authors = Counter()
top = Counter()
source_ids = Counter()
work_ids = Counter()
title_author = Counter()
rights_map = {r['work_id']: r for r in rights}
missing_rights = 0
lang_counts = Counter()
missing_language_evidence = 0

for entry in manifest:
    authors[entry['author']] += 1
    top[entry['author']] += entry.get('estimated_tokens', 0)
    cats[entry['category']] += entry.get('estimated_tokens', 0)
    source_ids[entry['source_id']] += 1
    work_ids[entry['work_id']] += 1
    title_author[(entry['title'].strip().lower(), entry['author'].strip().lower())] += 1
    if entry['work_id'] not in rights_map:
        missing_rights += 1
    evidence_entry = evidence.get('works', {}).get(entry['work_id'])
    if not evidence_entry:
        missing_language_evidence += 1
        lang_counts['MISSING'] += 1
    else:
        lang_counts[evidence_entry.get('status', 'MISSING')] += 1

print('recomputed_authors', len(authors))
print('recomputed_tokens', sum(cats.values()))
print('recomputed_category_tokens', dict(cats))
print('recomputed_fiction_pct', round(cats.get('FICTION', 0) / sum(cats.values()) * 100, 1) if cats else 0)
print('recomputed_essays_pct', round(cats.get('ESSAYS_GENERAL_NONFICTION', 0) / sum(cats.values()) * 100, 1) if cats else 0)
print('recomputed_science_pct', round(cats.get('SCIENCE_EDUCATION', 0) / sum(cats.values()) * 100, 1) if cats else 0)

top_author_name, top_author_tokens = top.most_common(1)[0]
print('top_author_name', top_author_name)
print('top_author_tokens', top_author_tokens)
print('top_author_pct', round(top_author_tokens / sum(cats.values()) * 100, 1) if cats else 0)
count_top10 = max(1, int(len(authors) * 0.1))
print('top10_pct', round(sum(v for _, v in top.most_common(count_top10)) / sum(cats.values()) * 100, 1) if cats else 0)

print('duplicate_source_ids', sum(1 for v in source_ids.values() if v > 1))
print('duplicate_work_ids', sum(1 for v in work_ids.values() if v > 1))
print('duplicate_title_author', sum(1 for v in title_author.values() if v > 1))
print('primary_reserve_overlap', len({entry['work_id'] for entry in manifest} & {entry['work_id'] for entry in reserve}))
print('missing_rights', missing_rights)
print('lang_counts', dict(lang_counts))
print('missing_language_evidence', missing_language_evidence)

print('\n=== DOWNLOAD PLAN CONSISTENCY ===')
manifest_source_ids = {entry['source_id'] for entry in manifest}
download_source_ids = {entry['source_id'] for entry in download}
print('download_entries', len(download))
print('download_match', manifest_source_ids == download_source_ids)
print('download_missing', sorted(manifest_source_ids - download_source_ids)[:10])
print('download_extra', sorted(download_source_ids - manifest_source_ids)[:10])
bad_urls = []
for entry in download:
    url = entry.get('url', '')
    if not url.startswith(('http://', 'https://')) or any(tok in url.lower() for tok in ['@', 'api_key', 'token=', 'password', 'secret']):
        bad_urls.append((entry.get('source_id'), url))
print('download_bad_urls', bad_urls[:20])

print('\n=== PREFLIGHT STATUS ===')
result = subprocess.run(['python', str(root / 'nexa-model' / 'scripts' / 'phase3e7_preflight.py')], capture_output=True, text=True)
print('preflight_exit_code', result.returncode)
print('preflight_stdout', result.stdout.strip())
print('preflight_stderr', result.stderr.strip())

print('\n=== TESTS ===')
for t in ['nexa-model/tests/test_language_verification.py', 'nexa-model/tests/test_select_pd5m_v6.py']:
    res = subprocess.run(['python', '-m', 'pytest', t, '-q'], capture_output=True, text=True)
    print('test_file', t, 'exit', res.returncode)
    print(res.stdout)
    print(res.stderr)

print('\n=== NEGATIVE PREFLIGHT TESTS ===')
with tempfile.TemporaryDirectory() as tmpdir:
    tmp_root = pathlib.Path(tmpdir)
    # replicate minimal tree
    (tmp_root / 'nexa-model' / 'scripts').mkdir(parents=True)
    (tmp_root / 'data' / 'proposals' / 'pd5m_v6').mkdir(parents=True)
    (tmp_root / 'data' / 'catalog').mkdir(parents=True)
    shutil.copy2(root / 'nexa-model' / 'scripts' / 'phase3e7_preflight.py', tmp_root / 'nexa-model' / 'scripts' / 'phase3e7_preflight.py')
    for f in required_files:
        shutil.copy2(proposal_root / f, tmp_root / 'data' / 'proposals' / 'pd5m_v6' / f)
    shutil.copy2(root / 'data' / 'catalog' / 'work_language_evidence.json', tmp_root / 'data' / 'catalog' / 'work_language_evidence.json')

    def run_temp():
        proc = subprocess.run(['python', str(tmp_root / 'nexa-model' / 'scripts' / 'phase3e7_preflight.py')], capture_output=True, text=True)
        return proc.returncode, proc.stdout, proc.stderr

    (tmp_root / 'data' / 'proposals' / 'pd5m_v6' / 'rights_evidence.json').unlink()
    code1, _, _ = run_temp()
    print('missing_rights_exit', code1)
    shutil.copy2(proposal_root / 'rights_evidence.json', tmp_root / 'data' / 'proposals' / 'pd5m_v6' / 'rights_evidence.json')

    (tmp_root / 'data' / 'proposals' / 'pd5m_v6' / 'artifact_integrity.json').unlink()
    code2, _, _ = run_temp()
    print('missing_integrity_exit', code2)
    shutil.copy2(proposal_root / 'artifact_integrity.json', tmp_root / 'data' / 'proposals' / 'pd5m_v6' / 'artifact_integrity.json')

    tampered = json.load((tmp_root / 'data' / 'proposals' / 'pd5m_v6' / 'artifact_integrity.json').open('r', encoding='utf-8'))
    tampered['files']['statistics.json'] = '0' * 64
    (tmp_root / 'data' / 'proposals' / 'pd5m_v6' / 'artifact_integrity.json').write_text(json.dumps(tampered, indent=2), encoding='utf-8')
    code3, _, _ = run_temp()
    print('tampered_integrity_exit', code3)

print('=== END ===')
