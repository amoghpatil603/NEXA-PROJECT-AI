import json
from pathlib import Path

repo = Path(r"C:/Users/amogh/OneDrive/c++/project 2")
reserve = json.load(open(repo / "data" / "proposals" / "pd5m_v6" / "reserve.json", "r", encoding="utf-8"))
ids = {'42188', '42259', '1837', '86'}
for e in reserve:
    if e['source_id'] in ids:
        print('source_id', e['source_id'])
        for key in ['work_id', 'title', 'author', 'category', 'estimated_tokens', 'rights_filter_status', 'rights_evidence', 'language', 'translation_status', 'metadata_sources']:
            print(' ', key, e.get(key))
        print()
