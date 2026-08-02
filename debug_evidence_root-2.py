<<<<<<< HEAD
import json
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parent
path = root / 'data' / 'catalog' / 'work_language_evidence.json'
with path.open('r', encoding='utf-8') as f:
    data = json.load(f)
works = data.get('works', {})
counts = Counter()
methods = Counter()
sources = Counter()
lang_qids = Counter()
matched = 0

for wid, entry in works.items():
    status = entry.get('status', 'UNKNOWN')
    counts[status] += 1
    ev = entry.get('evidence', {})
    methods[ev.get('method')] += 1
    sources[ev.get('source', '')] += 1
    if ev.get('matched_label'):
        matched += 1
    if ev.get('language_qid'):
        lang_qids[ev.get('language_qid')] += 1

print('total works', len(works))
print('counts', counts)
print('methods', methods)
print('sources sample', list(sources.items())[:20])
print('matched_label count', matched)
print('lang_qids', dict(lang_qids))
print('sample confirmed english entries:')
for wid, entry in list(works.items())[:20]:
    if entry.get('status') == 'CONFIRMED_ENGLISH':
        print(wid, entry['source_id'], entry['evidence'])
        break
=======
import json
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parent
path = root / 'data' / 'catalog' / 'work_language_evidence.json'
with path.open('r', encoding='utf-8') as f:
    data = json.load(f)
works = data.get('works', {})
counts = Counter()
methods = Counter()
sources = Counter()
lang_qids = Counter()
matched = 0

for wid, entry in works.items():
    status = entry.get('status', 'UNKNOWN')
    counts[status] += 1
    ev = entry.get('evidence', {})
    methods[ev.get('method')] += 1
    sources[ev.get('source', '')] += 1
    if ev.get('matched_label'):
        matched += 1
    if ev.get('language_qid'):
        lang_qids[ev.get('language_qid')] += 1

print('total works', len(works))
print('counts', counts)
print('methods', methods)
print('sources sample', list(sources.items())[:20])
print('matched_label count', matched)
print('lang_qids', dict(lang_qids))
print('sample confirmed english entries:')
for wid, entry in list(works.items())[:20]:
    if entry.get('status') == 'CONFIRMED_ENGLISH':
        print(wid, entry['source_id'], entry['evidence'])
        break
>>>>>>> origin/main
