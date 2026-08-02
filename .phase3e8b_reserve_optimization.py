import json
from pathlib import Path
from collections import Counter, defaultdict
from itertools import combinations
import math

repo = Path(r"C:/Users/amogh/OneDrive/c++/project 2")
reserve = json.load(open(repo / "data" / "proposals" / "pd5m_v6" / "reserve.json", "r", encoding="utf-8"))
clean = json.load(open(repo / "data" / "acquisition" / "pd5m_v6" / "clean_manifest.json", "r", encoding="utf-8"))
manifest = json.load(open(repo / "data" / "proposals" / "pd5m_v6" / "manifest.json", "r", encoding="utf-8"))

manifest_by_source = {e['source_id']: e for e in manifest}

corpus_bytes = sum(e['clean_bytes'] for e in clean)
bytes_by_author = Counter()
bytes_by_category = Counter()
for e in clean:
    bytes_by_author[e['author']] += e['clean_bytes']
    bytes_by_category[e['category']] += e['clean_bytes']

print(f'corpus_entries={len(clean)} corpus_bytes={corpus_bytes}')
print(f'corpus_author_count={len(bytes_by_author)}')
print('top authors by clean bytes:')
for author, b in bytes_by_author.most_common(15):
    print(f'  {author}: {b} bytes, share={b/corpus_bytes:.6%}')
print('top10 share=', sum(b for _, b in bytes_by_author.most_common(10)) / corpus_bytes)
print('category distribution:')
for cat, b in sorted(bytes_by_category.items(), key=lambda x: x[1], reverse=True):
    print(f'  {cat}: {b} bytes, share={b/corpus_bytes:.6%}')

ratios = []
missing_estimate = []
for e in clean:
    source_id = e['source_id']
    manifest_entry = manifest_by_source.get(source_id)
    if manifest_entry and manifest_entry.get('estimated_tokens'):
        ratios.append(e['clean_bytes'] / manifest_entry['estimated_tokens'])
    else:
        missing_estimate.append(source_id)

ratios.sort()
print('ratio sample count', len(ratios))
for q in [0.0, 0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 1.0]:
    idx = min(len(ratios) - 1, int(q * len(ratios)))
    print(f'  q={q:.2f} ratio={ratios[idx]:.6f}')

p05 = ratios[max(0, int(0.05 * len(ratios)))]
p10 = ratios[max(0, int(0.1 * len(ratios)))]
p25 = ratios[max(0, int(0.25 * len(ratios)))]
print(f'using conservative projections p05={p05:.6f} p10={p10:.6f} p25={p25:.6f}')
print('missing estimate for acquired sources', len(missing_estimate), missing_estimate[:10])

eligible = [e for e in reserve if e['rights_filter_status'] == 'ELIGIBLE' and e['language'] == 'English' and not e['translation_status']]
print('eligible english reserve count', len(eligible))
print('eligible reserve categories', Counter(e['category'] for e in eligible))
print('eligible reserve unique authors', len({e['author'] for e in eligible}))

for e in eligible:
    e['proj_bytes_p05'] = int(math.floor(e['estimated_tokens'] * p05))
    e['proj_bytes_p10'] = int(math.floor(e['estimated_tokens'] * p10))
    e['proj_bytes_p25'] = int(math.floor(e['estimated_tokens'] * p25))
    e['reliability_score'] = float(e.get('quality_score', 0.0))

print('\nTop eligible candidates by p10 projection:')
for e in sorted(eligible, key=lambda x: (-x['proj_bytes_p10'], x['author'], x['source_id']))[:20]:
    print(f"{e['source_id']} {e['work_id']} {e['author']} {e['category']} tokens={e['estimated_tokens']} p05={e['proj_bytes_p05']} p10={e['proj_bytes_p10']} p25={e['proj_bytes_p25']} quality={e.get('quality_score')} new_author={'no' if e['author'] in bytes_by_author else 'yes'}")

pliny_author = 'Pliny, the Elder'
pliny_bytes = bytes_by_author[pliny_author]
print(f'\ncurrent Pliny bytes={pliny_bytes} share={pliny_bytes/corpus_bytes:.6%}')

# gate evaluation functions

def evaluate_combo(combo):
    added_bytes = sum(e['proj_bytes_p05'] for e in combo)
    total_bytes = corpus_bytes + added_bytes

    author_bytes = bytes_by_author.copy()
    category_bytes = bytes_by_category.copy()
    for e in combo:
        author_bytes[e['author']] += e['proj_bytes_p05']
        category_bytes[e['category']] += e['proj_bytes_p05']

    top_authors = author_bytes.most_common(11)
    top_author_name, top_author_bytes = top_authors[0]
    top_author_share = top_author_bytes / total_bytes
    top10_share = sum(b for _, b in top_authors[:10]) / total_bytes
    fiction_share = category_bytes.get('FICTION', 0) / total_bytes
    essays_share = category_bytes.get('ESSAYS_GENERAL_NONFICTION', 0) / total_bytes
    science_share = category_bytes.get('SCIENCE_EDUCATION', 0) / total_bytes
    author_count = len(author_bytes)
    other_author_shares = {author: b/total_bytes for author, b in author_bytes.items()}
    max_author_under_5 = all(share <= 0.05 for share in other_author_shares.values())

    return {
        'combo': combo,
        'added_bytes': added_bytes,
        'total_bytes': total_bytes,
        'top_author_name': top_author_name,
        'top_author_bytes': top_author_bytes,
        'top_author_share': top_author_share,
        'top10_share': top10_share,
        'fiction_share': fiction_share,
        'essays_share': essays_share,
        'science_share': science_share,
        'author_count': author_count,
        'passes': {
            'authors': author_count >= 60,
            'top_author': top_author_share <= 0.05,
            'top10': top10_share <= 0.40,
            'fiction': fiction_share <= 0.50,
            'essays': essays_share >= 0.15,
            'science': science_share >= 0.10,
            'author_shares': max_author_under_5,
        },
        'new_author_count': len({e['author'] for e in combo if e['author'] not in bytes_by_author}),
        'reliability_score': sum(e['reliability_score'] for e in combo),
    }

# evaluate combos up to 4 works, prioritize fewer works
best = []
for size in range(1, 5):
    valid = []
    for combo in combinations(eligible, size):
        metrics = evaluate_combo(combo)
        if all(metrics['passes'].values()):
            valid.append(metrics)
    print(f'valid combos of size {size}:', len(valid))
    if valid:
        valid.sort(key=lambda m: (
            m['added_bytes'],
            m['top_author_share'],
            m['fiction_share'],
            -m['new_author_count'],
            -m['reliability_score'],
            tuple(sorted(e['source_id'] for e in m['combo']))
        ))
        best = valid[:10]
        print(f'best {len(best)} combos for size {size}:')
        for metrics in best:
            ids = [e['source_id'] for e in metrics['combo']]
            authors = [e['author'] for e in metrics['combo']]
            print(f"  size={size} ids={ids} authors={authors} added_bytes={metrics['added_bytes']} total={metrics['total_bytes']} top_author={metrics['top_author_name']} {metrics['top_author_share']:.4%} top10={metrics['top10_share']:.4%} fiction={metrics['fiction_share']:.4%} essays={metrics['essays_share']:.4%} science={metrics['science_share']:.4%} new_authors={metrics['new_author_count']} authors_over_5={metrics['authors_over_5']}")
            for e in metrics['combo']:
                print(f"    {e['source_id']} {e['work_id']} {e['author']} tokens={e['estimated_tokens']} proj_bytes={e['proj_bytes_p05']} quality={e.get('quality_score')}")
        break

# If no small combo was found, evaluate a greedy add-by-projected-bytes strategy.
print('\nRunning greedy incremental selection by projected bytes...')
selected = []
cur_total = corpus_bytes
cur_author_bytes = bytes_by_author.copy()
for e in sorted(eligible, key=lambda x: (-x['proj_bytes_p05'], x['author'], x['source_id'])):
    potential_total = cur_total + e['proj_bytes_p05']
    potential_author_bytes = cur_author_bytes.copy()
    potential_author_bytes[e['author']] += e['proj_bytes_p05']
    top_author_name, top_author_bytes = potential_author_bytes.most_common(1)[0]
    top_author_share = top_author_bytes / potential_total
    top10_share = sum(b for _, b in potential_author_bytes.most_common(10)) / potential_total
    fiction_share = (bytes_by_category.get('FICTION', 0) + sum(x['proj_bytes_p05'] for x in selected if x['category'] == 'FICTION') + (e['proj_bytes_p05'] if e['category'] == 'FICTION' else 0)) / potential_total
    essays_share = (bytes_by_category.get('ESSAYS_GENERAL_NONFICTION', 0) + sum(x['proj_bytes_p05'] for x in selected if x['category'] == 'ESSAYS_GENERAL_NONFICTION') + (e['proj_bytes_p05'] if e['category'] == 'ESSAYS_GENERAL_NONFICTION' else 0)) / potential_total
    science_share = (bytes_by_category.get('SCIENCE_EDUCATION', 0) + sum(x['proj_bytes_p05'] for x in selected if x['category'] == 'SCIENCE_EDUCATION') + (e['proj_bytes_p05'] if e['category'] == 'SCIENCE_EDUCATION' else 0)) / potential_total
    if top_author_share > 0.05 or top10_share > 0.40:
        continue
    selected.append(e)
    cur_total = potential_total
    cur_author_bytes = potential_author_bytes
    if cur_author_bytes['Pliny, the Elder'] / cur_total <= 0.049 and len(cur_author_bytes) >= 60:
        break

if selected:
    print('greedy selected', len(selected), 'works, added bytes', sum(e['proj_bytes_p05'] for e in selected), 'total_bytes', cur_total)
    print('greedy top author', cur_author_bytes.most_common(1)[0], 'share', cur_author_bytes.most_common(1)[0][1]/cur_total)
    print('greedy top10 share', sum(b for _, b in cur_author_bytes.most_common(10))/cur_total)
    print('greedy fiction share', (bytes_by_category.get('FICTION', 0) + sum(e['proj_bytes_p05'] for e in selected if e['category'] == 'FICTION'))/cur_total)
    print('greedy essays share', (bytes_by_category.get('ESSAYS_GENERAL_NONFICTION', 0) + sum(e['proj_bytes_p05'] for e in selected if e['category'] == 'ESSAYS_GENERAL_NONFICTION'))/cur_total)
    print('greedy science share', (bytes_by_category.get('SCIENCE_EDUCATION', 0) + sum(e['proj_bytes_p05'] for e in selected if e['category'] == 'SCIENCE_EDUCATION'))/cur_total)
    print('selected sources', [e['source_id'] for e in selected])
else:
    print('greedy selection failed to find a feasible set under current constraints.')

if not best:
    print('No valid combo found with up to 4 works under conservative projection.')
