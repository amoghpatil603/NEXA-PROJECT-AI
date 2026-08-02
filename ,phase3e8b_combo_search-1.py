<<<<<<< HEAD
import json
from pathlib import Path
from collections import Counter
from itertools import combinations

repo = Path(r"C:/Users/amogh/OneDrive/c++/project 2")
reserve = json.load(open(repo / "data" / "proposals" / "pd5m_v6" / "reserve.json", "r", encoding="utf-8"))
clean = json.load(open(repo / "data" / "acquisition" / "pd5m_v6" / "clean_manifest.json", "r", encoding="utf-8"))
current_authors = {e['author'] for e in clean}

eligible = [e for e in reserve if e['rights_filter_status'] == 'ELIGIBLE' and e['language'] == 'English' and not e['translation_status']]
print('total eligible reserve', len(eligible))
print('all categories', Counter(e['category'] for e in eligible))
print('current authors', len(current_authors))

# projection ratio p95 from previous script
ratio = 21.39944
needed_bytes = 3957778.040816322

# filter candidates by new author and unique authors
new_authors = {e['author'] for e in eligible if e['author'] not in current_authors}
new_candidates = [e for e in eligible if e['author'] in new_authors]
print('new author eligible count', len(new_candidates))
print('new candidate categories', Counter(e['category'] for e in new_candidates))

# evaluate 2-work combos and 3-work combos
combo_results = []
for size in [2,3,4]:
    for combo in combinations(new_candidates, size):
        total_bytes = sum(e['estimated_tokens'] * ratio for e in combo)
        total_est = sum(e['estimated_tokens'] for e in combo)
        authors = {e['author'] for e in combo}
        top = max(Counter(e['author'] for e in combo).values())
        combo_results.append((size, total_bytes, total_est, len(authors), combo))

# sort by number works, then bytes asc, then unique authors desc, then category balance maybe by not all fiction
combo_results.sort(key=lambda x: (x[0], x[1], -x[3], x[2]))

valid = [c for c in combo_results if c[1] >= needed_bytes]
print('valid combos', len(valid))
for c in valid[:20]:
    size, bytes_, est, uniq_authors, combo = c
    print('size',size,'bytes',round(bytes_), 'est',est,'uniq_authors',uniq_authors,'authors',[e['author'] for e in combo], 'ids',[e['source_id'] for e in combo])

# check two-work combos with 100k tokens only
h100 = [e for e in new_candidates if e['estimated_tokens'] == 100000]
print('100k new candidates', len(h100), Counter(e['author'] for e in h100)[:20] if False else '...')
for c in combinations(h100, 2):
    total_bytes = sum(e['estimated_tokens'] * ratio for e in c)
    authors = {e['author'] for e in c}
    if total_bytes >= needed_bytes:
        print('100k pair', [e['source_id'] for e in c], [e['author'] for e in c], 'bytes', round(total_bytes))
        break
=======
import json
from pathlib import Path
from collections import Counter
from itertools import combinations

repo = Path(r"C:/Users/amogh/OneDrive/c++/project 2")
reserve = json.load(open(repo / "data" / "proposals" / "pd5m_v6" / "reserve.json", "r", encoding="utf-8"))
clean = json.load(open(repo / "data" / "acquisition" / "pd5m_v6" / "clean_manifest.json", "r", encoding="utf-8"))
current_authors = {e['author'] for e in clean}

eligible = [e for e in reserve if e['rights_filter_status'] == 'ELIGIBLE' and e['language'] == 'English' and not e['translation_status']]
print('total eligible reserve', len(eligible))
print('all categories', Counter(e['category'] for e in eligible))
print('current authors', len(current_authors))

# projection ratio p95 from previous script
ratio = 21.39944
needed_bytes = 3957778.040816322

# filter candidates by new author and unique authors
new_authors = {e['author'] for e in eligible if e['author'] not in current_authors}
new_candidates = [e for e in eligible if e['author'] in new_authors]
print('new author eligible count', len(new_candidates))
print('new candidate categories', Counter(e['category'] for e in new_candidates))

# evaluate 2-work combos and 3-work combos
combo_results = []
for size in [2,3,4]:
    for combo in combinations(new_candidates, size):
        total_bytes = sum(e['estimated_tokens'] * ratio for e in combo)
        total_est = sum(e['estimated_tokens'] for e in combo)
        authors = {e['author'] for e in combo}
        top = max(Counter(e['author'] for e in combo).values())
        combo_results.append((size, total_bytes, total_est, len(authors), combo))

# sort by number works, then bytes asc, then unique authors desc, then category balance maybe by not all fiction
combo_results.sort(key=lambda x: (x[0], x[1], -x[3], x[2]))

valid = [c for c in combo_results if c[1] >= needed_bytes]
print('valid combos', len(valid))
for c in valid[:20]:
    size, bytes_, est, uniq_authors, combo = c
    print('size',size,'bytes',round(bytes_), 'est',est,'uniq_authors',uniq_authors,'authors',[e['author'] for e in combo], 'ids',[e['source_id'] for e in combo])

# check two-work combos with 100k tokens only
h100 = [e for e in new_candidates if e['estimated_tokens'] == 100000]
print('100k new candidates', len(h100), Counter(e['author'] for e in h100)[:20] if False else '...')
for c in combinations(h100, 2):
    total_bytes = sum(e['estimated_tokens'] * ratio for e in c)
    authors = {e['author'] for e in c}
    if total_bytes >= needed_bytes:
        print('100k pair', [e['source_id'] for e in c], [e['author'] for e in c], 'bytes', round(total_bytes))
        break
>>>>>>> origin/main
PY