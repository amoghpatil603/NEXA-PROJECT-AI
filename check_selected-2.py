<<<<<<< HEAD
import json

reserve = json.load(open('data/proposals/pd5m_v6/reserve.json', 'r', encoding='utf-8'))

ids = ['1837', '86', '42188', '42259', '696', '121', '22962', '26301', '940', '599', '25344', '580']
found = []
for e in reserve:
    if e['source_id'] in ids:
        found.append(e['source_id'])
        tok = e.get('estimated_tokens', 75000)
        est_bytes = tok * 4
        print(f"{e['source_id']}: {e['title'][:50]}... by {e['author']} | CAT={e['category']} | RIGHTS={e['rights_filter_status']} | EST={tok} tok ({est_bytes:,} bytes)")

missing = [i for i in ids if i not in found]
if missing:
    print(f"\nMISSING from reserve: {missing}")
else:
    print(f"\nAll {len(ids)} works verified in reserve.")

# Also check if these IDs are already in the corpus
clean = json.load(open('data/acquisition/pd5m_v6/clean_manifest.json', 'r', encoding='utf-8'))
clean_ids = set(e['source_id'] for e in clean)
existing = [i for i in ids if i in clean_ids]
if existing:
    print(f"\nWARNING: Works already in corpus: {existing}")
else:
    print(f"\nNone of the selected works are already in the corpus.")

# Count pliny-related works
pliny_works = [e for e in clean if e.get('author') == 'Pliny, the Elder']
print(f"\nPliny works in corpus: {len(pliny_works)}")
for pw in pliny_works:
=======
import json

reserve = json.load(open('data/proposals/pd5m_v6/reserve.json', 'r', encoding='utf-8'))

ids = ['1837', '86', '42188', '42259', '696', '121', '22962', '26301', '940', '599', '25344', '580']
found = []
for e in reserve:
    if e['source_id'] in ids:
        found.append(e['source_id'])
        tok = e.get('estimated_tokens', 75000)
        est_bytes = tok * 4
        print(f"{e['source_id']}: {e['title'][:50]}... by {e['author']} | CAT={e['category']} | RIGHTS={e['rights_filter_status']} | EST={tok} tok ({est_bytes:,} bytes)")

missing = [i for i in ids if i not in found]
if missing:
    print(f"\nMISSING from reserve: {missing}")
else:
    print(f"\nAll {len(ids)} works verified in reserve.")

# Also check if these IDs are already in the corpus
clean = json.load(open('data/acquisition/pd5m_v6/clean_manifest.json', 'r', encoding='utf-8'))
clean_ids = set(e['source_id'] for e in clean)
existing = [i for i in ids if i in clean_ids]
if existing:
    print(f"\nWARNING: Works already in corpus: {existing}")
else:
    print(f"\nNone of the selected works are already in the corpus.")

# Count pliny-related works
pliny_works = [e for e in clean if e.get('author') == 'Pliny, the Elder']
print(f"\nPliny works in corpus: {len(pliny_works)}")
for pw in pliny_works:
>>>>>>> origin/main
    print(f"  {pw['source_id']}: {pw['title'][:60]} - {pw['clean_bytes']:,} bytes")