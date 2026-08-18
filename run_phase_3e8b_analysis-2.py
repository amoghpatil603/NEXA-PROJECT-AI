import json
import math
from pathlib import Path
from collections import defaultdict, Counter

repo = Path(r"C:\Users\amogh\OneDrive\c++\project 2")
clean_path = repo / "data" / "acquisition" / "pd5m_v6" / "clean_manifest.json"
reserve_path = repo / "data" / "proposals" / "pd5m_v6" / "reserve.json"
manifest_path = repo / "data" / "proposals" / "pd5m_v6" / "manifest.json"
down_ledger_path = repo / "data" / "acquisition" / "pd5m_v6" / "download_ledger.jsonl"
raw_checksums_path = repo / "data" / "acquisition" / "pd5m_v6" / "raw_checksums.json"
clean_checksums_path = repo / "data" / "acquisition" / "pd5m_v6" / "clean_checksums.json"

clean = json.load(open(clean_path, 'r', encoding='utf-8'))
reserve = json.load(open(reserve_path, 'r', encoding='utf-8'))
manifest = json.load(open(manifest_path, 'r', encoding='utf-8'))

# Step 1: Exact bytes
bytes_by_author = defaultdict(int)
bytes_by_category = defaultdict(int)
for e in clean:
    author = e.get('author', 'UNKNOWN')
    cat = e.get('category', 'UNKNOWN')
    cb = e['clean_bytes']
    bytes_by_author[author] += cb
    bytes_by_category[cat] += cb

T = sum(e['clean_bytes'] for e in clean)
pliny_bytes = bytes_by_author.get("Pliny, the Elder", 0)
current_share = pliny_bytes / T

required_total_5 = math.ceil(pliny_bytes / 0.05)
minimum_addition_5 = required_total_5 - T
required_total_49 = math.ceil(pliny_bytes / 0.049)
minimum_addition_49 = required_total_49 - T

print(f"=== STEP 1: EXACT BYTES ===")
print(f"T (total clean bytes): {T:,}")
print(f"P (Pliny clean bytes): {pliny_bytes:,}")
print(f"Current Pliny share: {current_share*100:.4f}%")
print(f"Required total for <=5%: {required_total_5:,}")
print(f"Minimum addition for <=5%: {minimum_addition_5:,}")
print(f"Required total for <=4.9%: {required_total_49:,}")
print(f"Minimum addition for <=4.9%: {minimum_addition_49:,}")

# Step 2: Reserve analysis
eligible = [e for e in reserve if e['rights_filter_status'] == 'ELIGIBLE' and e['language'] == 'English' and not e['translation_status']]
eligible_by_cat = Counter(e['category'] for e in eligible)
fic_candidates = [e for e in eligible if e['category'] == 'FICTION']
nonfic_candidates = [e for e in eligible if e['category'] != 'FICTION']

print(f"\n=== STEP 2: RESERVE ANALYSIS ===")
print(f"Eligible reserve candidates: {len(eligible)}")
print(f"FICTION: {len(fic_candidates)}, NON-FICTION: {len(nonfic_candidates)}")
print(f"By category: {dict(eligible_by_cat)}")

# Step 3: Category headroom
current_fiction = bytes_by_category.get('FICTION', 0)
current_essays = bytes_by_category.get('ESSAYS_GENERAL_NONFICTION', 0)
current_science = bytes_by_category.get('SCIENCE_EDUCATION', 0)

print(f"\n=== STEP 3: CATEGORY HEADROOM ===")
for cat, b in sorted(bytes_by_category.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {b:,} ({b/T*100:.2f}%)")

# fiction <= 50%: (current_fiction + F) / (T + F) <= 0.5
max_f_by_fiction = max(0, T - 2 * current_fiction)
# essays >= 15%: current_essays / (T + F) >= 0.15
max_f_by_essays = max(0, (current_essays - 0.15 * T) / 0.15)
# science >= 10%: current_science / (T + F) >= 0.10
max_f_by_science = max(0, (current_science - 0.10 * T) / 0.10)

max_safe_fiction = min(max_f_by_fiction, max_f_by_essays, max_f_by_science)
limiting = None
for name, val in [("fiction<=50%", max_f_by_fiction), ("essays>=15%", max_f_by_essays), ("science>=10%", max_f_by_science)]:
    if abs(val - max_safe_fiction) < 1:
        limiting = name

print(f"Max fiction by fiction<=50%: {max_f_by_fiction:,.0f}")
print(f"Max fiction by essays>=15%: {max_f_by_essays:,.0f}")
print(f"Max fiction by science>=10%: {max_f_by_science:,.0f}")
print(f"Max safe fiction addition: {int(max_safe_fiction):,}")
print(f"Limiting gate: {limiting}")
print(f"min_addition_5: {minimum_addition_5:,}")
print(f"min_addition_49: {minimum_addition_49:,}")
print(f"Within headroom for <=5%: {minimum_addition_5 <= max_safe_fiction}")
print(f"Within headroom for <=4.9%: {minimum_addition_49 <= max_safe_fiction}")

# Author analysis
author_list = sorted(bytes_by_author.items(), key=lambda x: -x[1])
top10_bytes = sum(b for _, b in author_list[:10])
print(f"\n=== AUTHOR CONCENTRATION ===")
print(f"Unique authors: {len(author_list)}")
for name, b in author_list[:10]:
    print(f"  {name}: {b:,} ({b/T*100:.3f}%)")
print(f"Top-10 share: {top10_bytes/T*100:.2f}%")

# Step 7: 26225
print(f"\n=== PRIMARY 26225 ===")
download_ledger = []
with open(down_ledger_path, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            download_ledger.append(json.loads(line))
failed = [r for r in download_ledger if r['status'] == 'FAILED']
for r in failed:
    print(f"  source_id: {r['source_id']}, title: {r.get('title','')}, reason: {r.get('reason','N/A')}")

# Step 8: Integrity
print(f"\n=== INTEGRITY ===")
raw_cs = json.load(open(raw_checksums_path, 'r', encoding='utf-8'))
clean_cs = json.load(open(clean_checksums_path, 'r', encoding='utf-8'))
accepted_ids = set(e['source_id'] for e in clean)
raw_ids = set(raw_cs.keys())
clean_ids = set(clean_cs.keys())
print(f"Accepted: {len(accepted_ids)}, RAW checksums: {len(raw_ids)}, CLEAN checksums: {len(clean_cs)}")
print(f"RAW coverage: {len(accepted_ids & raw_ids)}/{len(accepted_ids)}")
print(f"CLEAN coverage: {len(accepted_ids & clean_ids)}/{len(accepted_ids)}")
missing_raw = accepted_ids - raw_ids
missing_clean = accepted_ids - clean_ids
if missing_raw:
    print(f"Missing RAW: {sorted(missing_raw)}")
if missing_clean:
    print(f"Missing CLEAN: {sorted(missing_clean)}")

# Build failure analysis JSON
failure_analysis = {
    "current_state": {
        "clean_byte_total": T,
        "pliny_clean_bytes": pliny_bytes,
        "pliny_share_pct": round(current_share * 100, 4),
        "min_addition_5_pct_bytes": minimum_addition_5,
        "min_addition_49_pct_bytes": minimum_addition_49,
        "works": len(clean),
        "authors": len(author_list),
        "top_10_share_pct": round(top10_bytes / T * 100, 2),
    },
    "category_distribution": {cat: round(b/T*100, 2) for cat, b in sorted(bytes_by_category.items(), key=lambda x: -x[1])},
    "eligible_reserve": {
        "total": len(eligible),
        "fiction": len(fic_candidates),
        "non_fiction": len(nonfic_candidates),
        "by_category": dict(eligible_by_cat),
    },
    "category_headroom": {
        "max_fiction_by_fiction_gate": int(max_f_by_fiction),
        "max_fiction_by_essays_gate": int(max_f_by_essays),
        "max_fiction_by_science_gate": int(max_f_by_science),
        "max_safe_fiction_addition": int(max_safe_fiction),
        "limiting_gate": limiting,
        "min_addition_5_within_capacity": minimum_addition_5 <= max_safe_fiction,
        "min_addition_49_within_capacity": minimum_addition_49 <= max_safe_fiction,
    },
    "reserve_works_search_failure": {
        "root_cause": "fiction_dilution",
        "explanation": "All 62 eligible reserve candidates are FICTION. Adding enough fiction to reduce Pliny below 5% would dilute essays below 15% or science below 10%, or push fiction above 50%.",
        "all_reserve_is_fiction": len(nonfic_candidates) == 0,
        "current_fiction_pct": round(current_fiction / T * 100, 2),
        "current_essays_pct": round(current_essays / T * 100, 2),
        "current_science_pct": round(current_science / T * 100, 2),
    },
    "primary_26225": {
        "work_id": "pd_26225",
        "title": "Fifteen Thousand Useful Phrases",
        "author": "Kleiser, Grenville",
        "status": "FAILED",
        "attempt_count": 35,
        "404_root_cause": "All standard Gutenberg txt endpoints returned 404. This PG ebook may have been removed or never had a txt version.",
        "category": "ESSAYS_GENERAL_NONFICTION",
        "estimated_tokens": 100000,
        "recoverable": False,
    },
    "integrity": {
        "accepted_raw_count": len(accepted_ids),
        "raw_checksum_count": len(raw_ids),
        "clean_checksum_count": len(clean_cs),
        "raw_coverage_pct": round(len(accepted_ids & raw_ids) / len(accepted_ids) * 100, 1),
        "clean_coverage_pct": round(len(accepted_ids & clean_ids) / len(accepted_ids) * 100, 1),
        "missing_raw_checksums": sorted(missing_raw),
        "missing_clean_checksums": sorted(missing_clean),
        "failed_primaries": [{"source_id": r['source_id'], "title": r.get('title', ''), "reason": r.get('reason', '')} for r in failed],
    }
}

output_path = repo / "data" / "reports" / "phase_3e8b_reserve_failure_analysis.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(failure_analysis, f, indent=2)
print(f"\nFailure analysis written to: {output_path}")

# Determine if reserve can repair
print(f"\n=== CONCLUSION ===")
if len(nonfic_candidates) > 0:
    print("Non-fiction candidates exist - could help fix category balance.")
else:
    print("ALL ELIGIBLE RESERVE IS FICTION.")
    print("Fiction-only reserve cannot repair without breaking essays/science gates.")
    print("EXPANSION NEEDED: add non-fiction candidates (ESSAYS, SCIENCE, HISTORY).")

# Calculate required non-fiction
required_essays_for_49 = max(0, 0.15 * (T + minimum_addition_49) - current_essays)
required_science_for_49 = max(0, 0.10 * (T + minimum_addition_49) - current_science)
print(f"\nRequired additional essays for <=4.9%: {required_essays_for_49:,.0f} bytes")
print(f"Required additional science for <=4.9%: {required_science_for_49:,.0f} bytes")
print(f"Total non-fiction needed: {required_essays_for_49 + required_science_for_49:,.0f} bytes")