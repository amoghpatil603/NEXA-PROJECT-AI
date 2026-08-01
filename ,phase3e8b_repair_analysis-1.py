import json
from pathlib import Path
from collections import Counter
import statistics

repo = Path(r"C:/Users/amogh/OneDrive/c++/project 2")
clean = json.load(open(repo / "data" / "acquisition" / "pd5m_v6" / "clean_manifest.json", "r", encoding="utf-8"))
reserve = json.load(open(repo / "data" / "proposals" / "pd5m_v6" / "reserve.json", "r", encoding="utf-8"))
manifest = json.load(open(repo / "data" / "proposals" / "pd5m_v6" / "manifest.json", "r", encoding="utf-8"))

manifest_by_source = {entry['source_id']: entry for entry in manifest}
ratios = []
for e in clean:
    est = manifest_by_source.get(e['source_id'], {}).get('estimated_tokens')
    if not est:
        continue
    b = len(Path(e['clean_path']).read_bytes())
    ratios.append(b / est)

print('ratio_count', len(ratios))
print('ratio_min', min(ratios))
print('ratio_max', max(ratios))
print('ratio_mean', statistics.mean(ratios))
print('ratio_median', statistics.median(ratios))
print('ratio_p90', sorted(ratios)[int(len(ratios) * 0.9)])
print('ratio_p95', sorted(ratios)[int(len(ratios) * 0.95)])
print('ratio_p99', sorted(ratios)[int(len(ratios) * 0.99)])

reserve_cats = Counter(e.get('category', '') for e in reserve)
reserve_authors = Counter(e['author'] for e in reserve)
reserve_new = [e for e in reserve if e['author'] not in {x['author'] for x in clean}]
print('reserve_count', len(reserve))
print('reserve_new_count', len(reserve_new))
print('reserve_new_authors', len({e['author'] for e in reserve_new}))
print('reserve_categories', reserve_cats)
print('reserve_top_authors', reserve_authors.most_common(20))

# Candidate projection using conservative ratio (p95)
ratio = sorted(ratios)[int(len(ratios) * 0.95)]
print('projection_ratio', ratio)

current_bytes = sum(len(Path(e['clean_path']).read_bytes()) for e in clean)
current_top_bytes = Counter()
for e in clean:
    current_top_bytes[e['author']] += len(Path(e['clean_path']).read_bytes())
top_author = current_top_bytes.most_common(1)[0]
required_total_5 = top_author[1] / 0.05
required_total_4_9 = top_author[1] / 0.049
needed_5 = required_total_5 - current_bytes
needed_4_9 = required_total_4_9 - current_bytes
print('current_bytes', current_bytes)
print('top_author', top_author)
print('required_total_5', required_total_5)
print('required_total_4_9', required_total_4_9)
print('needed_5', needed_5)
print('needed_4_9', needed_4_9)

candidates = []
for e in reserve_new:
    est = e.get('estimated_tokens')
    if not est:
        continue
    proj_bytes = est * ratio
    candidates.append((proj_bytes, e))
candidates.sort(reverse=True, key=lambda x: x[0])

acc = 0
sel = []
for proj_bytes, e in candidates:
    sel.append((proj_bytes, e))
    acc += proj_bytes
    if acc >= needed_4_9:
        break

print('selected_count', len(sel))
print('selected_proj_bytes', acc)
for b, e in sel[:20]:
    print(e['source_id'], e['author'], e['category'], e['estimated_tokens'], round(b))
print('selected categories', Counter(e['category'] for _, e in sel))
print('selected new authors', len({e['author'] for _, e in sel}))
print('selected total_estimated_tokens', sum(e['estimated_tokens'] for _, e in sel))
print('selected largest', sorted([(round(b), e['source_id']) for b, e in sel], reverse=True)[:10])
