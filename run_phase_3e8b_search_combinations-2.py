import json
import math
from pathlib import Path
from collections import defaultdict

repo = Path(r"C:\Users\amogh\OneDrive\c++\project 2")
clean_path = repo / "data" / "acquisition" / "pd5m_v6" / "clean_manifest.json"
reserve_path = repo / "data" / "proposals" / "pd5m_v6" / "reserve.json"
manifest_path = repo / "data" / "proposals" / "pd5m_v6" / "manifest.json"

clean = json.load(open(clean_path, 'r', encoding='utf-8'))
reserve = json.load(open(reserve_path, 'r', encoding='utf-8'))

# Get current bytes by author and category
bytes_by_author = defaultdict(int)
bytes_by_category = defaultdict(int)
for e in clean:
    bytes_by_author[e.get('author', 'UNKNOWN')] += e['clean_bytes']
    bytes_by_category[e.get('category', 'UNKNOWN')] += e['clean_bytes']

T = sum(e['clean_bytes'] for e in clean)
print(f"Current total bytes: {T:,}")
print(f"Current fiction bytes: {bytes_by_category.get('FICTION',0):,} ({bytes_by_category.get('FICTION',0)/T*100:.2f}%)")
print(f"Current essays bytes: {bytes_by_category.get('ESSAYS_GENERAL_NONFICTION',0):,} ({bytes_by_category.get('ESSAYS_GENERAL_NONFICTION',0)/T*100:.2f}%)")
print(f"Current science bytes: {bytes_by_category.get('SCIENCE_EDUCATION',0):,} ({bytes_by_category.get('SCIENCE_EDUCATION',0)/T*100:.2f}%)")

# Get existing authors who have fiction in the corpus
# Build mapping of author -> [works in current corpus]
author_current_works = defaultdict(list)
for e in clean:
    author = e.get('author', 'UNKNOWN')
    cat = e.get('category', 'UNKNOWN')
    author_current_works[author].append(e)

# Get fiction authors with their current bytes
fiction_authors_current = {}
for author, works in author_current_works.items():
    fic_bytes = sum(w['clean_bytes'] for w in works if w.get('category') == 'FICTION')
    if fic_bytes > 0:
        fiction_authors_current[author] = fic_bytes

print(f"\nExisting fiction authors in corpus:")
for auth, b in sorted(fiction_authors_current.items(), key=lambda x: -x[1]):
    print(f"  {auth}: {b:,} ({b/T*100:.3f}%)")

# Group reserve candidates by author
reserve_by_author = defaultdict(list)
for e in reserve:
    if e.get('rights_filter_status') == 'ELIGIBLE' and e.get('category') == 'FICTION':
        auth = e.get('author', 'UNKNOWN')
        est_bytes = e.get('estimated_tokens', 75000) * 4  # ~4 bytes per token
        reserve_by_author[auth].append({'work': e, 'est_bytes': est_bytes})

print(f"\nReserve candidates by author:")
for auth, works in sorted(reserve_by_author.items(), key=lambda x: -sum(w['est_bytes'] for w in x[1])):
    total_est = sum(w['est_bytes'] for w in works)
    print(f"  {auth}: {len(works)} works, ~{total_est:,} bytes total")

# Strategy: sort all reserve works by size (largest first reduces needed count)
all_works_by_size = []
for e in reserve:
    if e.get('rights_filter_status') == 'ELIGIBLE' and e.get('category') == 'FICTION':
        est_bytes = e.get('estimated_tokens', 75000) * 4
        all_works_by_size.append({'work': e, 'est_bytes': est_bytes})

all_works_by_size.sort(key=lambda x: -x['est_bytes'])  # largest first

# Now simulate adding works incrementally and check all gates
def simulate_addition(selected_works):
    """Simulate adding works and check all gates"""
    added_bytes = sum(w['est_bytes'] for w in selected_works)
    new_T = T + added_bytes
    
    # Count bytes by author (existing + new)
    new_author_bytes = defaultdict(int, bytes_by_author)
    new_category_bytes = defaultdict(int, bytes_by_category)
    
    for w in selected_works:
        work = w['work']
        auth = work.get('author', 'UNKNOWN')
        cat = work.get('category', 'UNKNOWN')
        est = w['est_bytes']
        new_author_bytes[auth] += est
        new_category_bytes[cat] += est
    
    # Check gates
    top_author = max(new_author_bytes.items(), key=lambda x: x[1])
    top_author_pct = top_author[1] / new_T * 100
    
    top10 = sum(b for _, b in sorted(new_author_bytes.items(), key=lambda x: -x[1])[:10])
    top10_pct = top10 / new_T * 100
    
    fiction_pct = new_category_bytes.get('FICTION', 0) / new_T * 100
    essays_pct = new_category_bytes.get('ESSAYS_GENERAL_NONFICTION', 0) / new_T * 100
    science_pct = new_category_bytes.get('SCIENCE_EDUCATION', 0) / new_T * 100
    
    authors = len(new_author_bytes)
    
    # Check if Pliny is still top
    pliny_bytes = new_author_bytes.get("Pliny, the Elder", 0)
    pliny_pct = pliny_bytes / new_T * 100
    
    # Find any author exceeding 5%
    over_5 = [(n, b/new_T*100) for n, b in new_author_bytes.items() if b/new_T > 0.05]
    
    gates = {
        'works': len(clean) + len(selected_works),
        'authors': authors,
        'total_bytes': new_T,
        'added_bytes': added_bytes,
        'top_author': top_author[0],
        'top_author_pct': round(top_author_pct, 4),
        'top10_pct': round(top10_pct, 2),
        'fiction_pct': round(fiction_pct, 2),
        'essays_pct': round(essays_pct, 2),
        'science_pct': round(science_pct, 2),
        'pliny_pct': round(pliny_pct, 4),
        'over_5_pct_authors': [(n, round(p, 4)) for n, p in over_5],
        'all_pass': (
            authors >= 60 and
            fiction_pct <= 50 and
            essays_pct >= 15 and
            science_pct >= 10 and
            top_author_pct <= 5 and
            top10_pct <= 40 and
            not over_5  # no author > 5%
        ),
        'pliny_under_5': pliny_pct <= 5,
        'pliny_under_49': pliny_pct <= 4.9,
    }
    return gates

# Try greedy: add largest works until <=5%
print(f"\n=== GREEDY SEARCH: Add largest works until <=5% ===")
selected_5 = []
for w in all_works_by_size:
    selected_5.append(w)
    gates = simulate_addition(selected_5)
    added = gates['added_bytes']
    used = len(selected_5)
    print(f"  {used} works, added {added:,} bytes: top={gates['top_author_pct']:.4f}%, pliny={gates['pliny_pct']:.4f}%, fic={gates['fiction_pct']:.1f}%, essay={gates['essays_pct']:.1f}%, sci={gates['science_pct']:.1f}%, pass={gates['all_pass']}")
    if gates['pliny_under_5']:
        print(f"\n  *** <=5% reached with {used} works! ***")
        print(f"  Added {added:,} bytes")
        print(f"  Top author: {gates['top_author']} at {gates['top_author_pct']:.4f}%")
        break

# Continue to <=4.9% if possible
selected_49 = list(selected_5)
if not gates['pliny_under_49']:
    for w in all_works_by_size[len(selected_5):]:
        selected_49.append(w)
        gates = simulate_addition(selected_49)
        used = len(selected_49)
        added = gates['added_bytes']
        print(f"  {used} works, added {added:,} bytes: pliny={gates['pliny_pct']:.4f}%, pass={gates['all_pass']}")
        if gates['pliny_under_49']:
            print(f"\n  *** <=4.9% reached with {used} works! ***")
            break

# Now find the AUTHOR-SAFE minimum combination
# Some existing fiction authors might exceed 5% if we add too many of their works
# Let's be more careful: prefer authors NOT already in corpus, or from authors with small existing share

# Build list of safe authors (existing share < 2% so adding one work won't exceed 5%)
safe_authors_reserve = {}
for e in reserve:
    if e.get('rights_filter_status') == 'ELIGIBLE' and e.get('category') == 'FICTION':
        auth = e.get('author', 'UNKNOWN')
        existing = bytes_by_author.get(auth, 0)
        est_bytes = e.get('estimated_tokens', 75000) * 4
        # An author is safe if existing + est_bytes doesn't exceed 5% of (T + est_bytes)
        # existing + est <= 0.05 * (T + est)
        # existing + est <= 0.05T + 0.05est
        # existing + 0.95est <= 0.05T
        if existing + 0.95 * est_bytes <= 0.05 * T:
            if auth not in safe_authors_reserve:
                safe_authors_reserve[auth] = []
            safe_authors_reserve[auth].append({'work': e, 'est_bytes': est_bytes, 'existing': existing})

print(f"\n=== CONCENTRATION-WARE SEARCH ===")
print(f"Authors with safe addition margin: {len(safe_authors_reserve)}")
for auth, works in sorted(safe_authors_reserve.items(), key=lambda x: -len(x[1])):
    existing = bytes_by_author.get(auth, 0)
    total_add = sum(w['est_bytes'] for w in works)
    print(f"  {auth}: existing={existing:,}, can add ~{total_add:,}")

# Try adding works from safe authors only (no author concentration risk)
safe_works = []
for auth, works in safe_authors_reserve.items():
    for w in works:
        safe_works.append(w)

safe_works.sort(key=lambda x: -x['est_bytes'])
print(f"\nSafe works available: {len(safe_works)}")

selected_safe = []
for w in safe_works:
    selected_safe.append(w)
    gates = simulate_addition(selected_safe)
    used = len(selected_safe)
    added = gates['added_bytes']
    print(f"  {used} works, added {added:,} bytes: top={gates['top_author_pct']:.4f}%, pliny={gates['pliny_pct']:.4f}%, pass={gates['all_pass']}")
    if gates['all_pass']:
        # Find the works used
        work_ids = [w['work']['source_id'] for w in selected_safe]
        work_details = []
        for w in selected_safe:
            work_details.append({
                'source_id': w['work']['source_id'],
                'title': w['work']['title'],
                'author': w['work']['author'],
                'est_bytes': w['est_bytes'],
            })
        
        print(f"\n*** ALL GATES PASS with {used} works! ***")
        print(f"Works: {work_ids}")
        print(f"Added bytes: {added:,}")
        print(f"Top author: {gates['top_author']} at {gates['top_author_pct']:.4f}%")
        print(f"Fiction: {gates['fiction_pct']:.1f}%")
        print(f"Essays: {gates['essays_pct']:.1f}%")
        print(f"Science: {gates['science_pct']:.1f}%")
        print(f"Top10: {gates['top10_pct']:.1f}%")
        break

# If no safe author combination works, try existing fiction authors but limit to avoid exceeding 5%
if not selected_safe or not simulate_addition(selected_safe)['all_pass']:
    print(f"\nSafe-only search incomplete. Trying broader search...")
    # For each existing fiction author, calculate how many reserve works can be added safely
    restricted_works = []
    for e in reserve:
        if e.get('rights_filter_status') == 'ELIGIBLE' and e.get('category') == 'FICTION':
            auth = e.get('author', 'UNKNOWN')
            existing = bytes_by_author.get(auth, 0)
            est_bytes = e.get('estimated_tokens', 75000) * 4
            restricted_works.append({'work': e, 'est_bytes': est_bytes, 'author': auth, 'existing': existing})
    
    restricted_works.sort(key=lambda x: -x['est_bytes'])
    
    # Simulate with author cap tracking
    def simulate_capped(selection):
        """Simulate but cap any single author's contribution"""
        new_author = defaultdict(int, bytes_by_author)
        new_cat = defaultdict(int, bytes_by_category)
        added = 0
        for w in selection:
            auth = w['author']
            cat = w['work']['category']
            est = w['est_bytes']
            new_author[auth] += est
            new_cat[cat] += est
            added += est
        
        new_T = T + added
        top = max(new_author.items(), key=lambda x: x[1])
        top_pct = top[1]/new_T*100
        over_5 = [(n, b/new_T*100) for n, b in new_author.items() if b/new_T > 0.05]
        
        return {
            'added': added,
            'top_author': top[0],
            'top_pct': top_pct,
            'over_5': over_5,
            'pliny_pct': new_author.get("Pliny, the Elder", 0) / new_T * 100,
            'fiction_pct': new_cat.get('FICTION', 0)/new_T*100,
            'essays_pct': new_cat.get('ESSAYS_GENERAL_NONFICTION', 0)/new_T*100,
            'science_pct': new_cat.get('SCIENCE_EDUCATION', 0)/new_T*100,
            'top10_pct': sum(b for _, b in sorted(new_author.items(), key=lambda x: -x[1])[:10])/new_T*100,
            'authors': len(new_author),
        }
    
    selection = []
    for w in restricted_works:
        selection.append(w)
        r = simulate_capped(selection)
        print(f"  {len(selection)} works, added {r['added']:,}: top={r['top_author']} {r['top_pct']:.4f}%, over5={r['over_5']}, pliny={r['pliny_pct']:.4f}%")
        if not r['over_5'] and r['pliny_pct'] <= 5:
            print(f"\n*** Clean pass with {len(selection)} works! ***")
            print(f"Added: {r['added']:,}")
            work_list = [{'source_id': w['work']['source_id'], 'title': w['work']['title'], 'author': w['author']} for w in selection]
            for wl in work_list:
                print(f"  {wl['source_id']}: {wl['title']} by {wl['author']}")
            break

print(f"\n=== DONE ===")