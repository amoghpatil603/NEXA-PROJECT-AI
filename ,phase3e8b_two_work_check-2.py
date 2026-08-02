import json
from pathlib import Path
repo = Path(r"C:/Users/amogh/OneDrive/c++/project 2")
clean = json.load(open(repo / "data" / "acquisition" / "pd5m_v6" / "clean_manifest.json", "r", encoding="utf-8"))
reserve = json.load(open(repo / "data" / "proposals" / "pd5m_v6" / "reserve.json", "r", encoding="utf-8"))
current_authors = {e['author'] for e in clean}
for author in ['Howard, Robert E. (Robert Ervin)', 'Twain, Mark']:
    print(author, 'present' if author in current_authors else 'absent')
print('authors in clean count', len(current_authors))
print('100k reserve authors', sorted({e['author'] for e in reserve if e['estimated_tokens']==100000}))
print('100k new reserve authors', sorted({e['author'] for e in reserve if e['estimated_tokens']==100000 and e['author'] not in current_authors}))
