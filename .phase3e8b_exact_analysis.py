import json
import math
from pathlib import Path
from collections import Counter

repo = Path(r"C:/Users/amogh/OneDrive/c++/project 2")
clean_path = repo / "data" / "acquisition" / "pd5m_v6" / "clean_manifest.json"
reserve_path = repo / "data" / "proposals" / "pd5m_v6" / "reserve.json"
manifest_path = repo / "data" / "proposals" / "pd5m_v6" / "manifest.json"
download_ledger_path = repo / "data" / "acquisition" / "pd5m_v6" / "download_ledger.jsonl"

clean = json.load(open(clean_path, 'r', encoding='utf-8'))
reserve = json.load(open(reserve_path, 'r', encoding='utf-8'))
manifest = json.load(open(manifest_path, 'r', encoding='utf-8'))
manifest_by_source = {e['source_id']: e for e in manifest}

T = sum(e['clean_bytes'] for e in clean)
bytes_by_author = Counter(e['clean_bytes'] for e in clean)
bytes_by_category = Counter(e['clean_bytes'] for e in clean)
P = bytes_by_author['Pliny, the Elder']
current_share = P / T
required_total_5 = math.ceil(P / 0.05)
minimum_addition_5 = required_total_5 - T
required_total_49 = math.ceil(P / 0.049)
minimum_addition_49 = required_total_49 - T

eligible = [e for e in reserve if e['rights_filter_status'] == 'ELIGIBLE' and e['language'] == 'English' and not e['translation_status']]
eligible_count = len(eligible)
eligible_by_author = Counter(e['author'] for e in eligible)
eligible_by_category = Counter(e['category'] for e in eligible)

# calculate safe fiction headroom for category gates
current_fiction = bytes_by_category.get('FICTION', 0)
current_essays = bytes_by_category.get('ESSAYS_GENERAL_NONFICTION', 0)
current_science = bytes_by_category.get('SCIENCE_EDUCATION', 0)
current_other_nonfiction = sum(bytes_by_category.get(cat, 0) for cat in bytes_by_category if cat != 'FICTION')

# fiction <= 50% means fiction_added <= 0.5*(T + fiction_added) - current_fiction? Let's derive precisely.
# Actually, after adding F fiction bytes: (current_fiction + F)/(T + F) <= 0.5 -> current_fiction + F <= 0.5 T + 0.5 F -> F <= T - 2*current_fiction
# Wait solve correctly: (f+c)/(T+f) <= 0.5 -> 2(current_fiction+F) <= T+F -> 2*current_fiction + 2F <= T + F -> F <= T - 2*current_fiction.
max_fiction_by_fiction = max(0, T - 2*current_fiction)
# essays >=15% after adding F fiction: current_essays/(T+F) >= 0.15 -> F <= (current_essays/0.15) - T
max_fiction_by_essays = max(0, math.floor(current_essays / 0.15 - T))
# science >=10%: current_science/(T+F) >=0.10 -> F <= (current_science/0.10) - T
max_fiction_by_science = max(0, math.floor(current_science / 0.10 - T))

max_safe_fiction_addition = min(max_fiction_by_fiction, max_fiction_by_essays, max_fiction_by_science)
limiting_gate = None
limit_values = {
    'fiction': max_fiction_by_fiction,
    'essays': max_fiction_by_essays,
    'science': max_fiction_by_science,
}
min_val = min(limit_values.values())
for gate, val in limit_values.items():
    if val == min_val:
        limiting_gate = gate
        break


download_ledger = []
with open(download_ledger_path, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            download_ledger.append(json.loads(line))

failed_primary = [rec for rec in download_ledger if rec.get('status') == 'FAILED_PRIMARY']
failed_primary_ids = [rec.get('source_id') for rec in failed_primary]

output = {
    'T': T,
    'P': P,
    'current_share': current_share,
    'required_total_5': required_total_5,
    'minimum_addition_5': minimum_addition_5,
    'required_total_49': required_total_49,
    'minimum_addition_49': minimum_addition_49,
    'eligible_count': eligible_count,
    'eligible_by_category': eligible_by_category,
    'eligible_by_author_top20': eligible_by_author.most_common(20),
    'max_fiction_by_fiction': max_fiction_by_fiction,
    'max_fiction_by_essays': max_fiction_by_essays,
    'max_fiction_by_science': max_fiction_by_science,
    'max_safe_fiction_addition': max_safe_fiction_addition,
    'limiting_gate': limiting_gate,
    'failed_primary': failed_primary_ids,
}
print(json.dumps(output, indent=2))
