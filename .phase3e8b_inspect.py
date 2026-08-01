import json
import re
from pathlib import Path
from collections import Counter

repo = Path(r"C:/Users/amogh/OneDrive/c++/project 2")
clean = json.load(open(repo / "data" / "acquisition" / "pd5m_v6" / "clean_manifest.json", "r", encoding="utf-8"))
reserve = json.load(open(repo / "data" / "proposals" / "pd5m_v6" / "reserve.json", "r", encoding="utf-8"))
ledger = [json.loads(line) for line in open(repo / "data" / "acquisition" / "pd5m_v6" / "download_ledger.jsonl", "r", encoding="utf-8") if line.strip()]
raw = json.load(open(repo / "data" / "acquisition" / "pd5m_v6" / "raw_checksums.json", "r", encoding="utf-8"))
cleancs = json.load(open(repo / "data" / "acquisition" / "pd5m_v6" / "clean_checksums.json", "r", encoding="utf-8"))
prov = json.load(open(repo / "data" / "acquisition" / "pd5m_v6" / "provenance.json", "r", encoding="utf-8"))

stats = {}
stats["works"] = len(clean)
stats["unique_authors"] = len({e["author"] for e in clean})
stats["clean_bytes"] = 0
stats["characters"] = 0
stats["words"] = 0
cats = Counter()
authors = Counter()
lang = Counter()
rights = Counter()
for e in clean:
    p = Path(e["clean_path"])
    t = p.read_text(encoding="utf-8")
    stats["clean_bytes"] += len(t.encode("utf-8"))
    stats["characters"] += len(t)
    stats["words"] += len(re.findall(r"\\w+", t))
    cats[e.get("category", "")] += len(t.encode("utf-8"))
    authors[e["author"]] += len(t.encode("utf-8"))
    lang[e["language_status"]] += 1
    rights[e["rights_status"]] += 1

stats["top_author"] = authors.most_common(1)[0][0]
stats["top_author_bytes"] = authors.most_common(1)[0][1]
stats["top_author_share"] = stats["top_author_bytes"] / stats["clean_bytes"] * 100
stats["top10_share"] = sum(v for _, v in authors.most_common(10)) / stats["clean_bytes"] * 100
stats["category_pct"] = {k: v / stats["clean_bytes"] * 100 for k, v in cats.items()}

print(json.dumps({
    "stats": stats,
    "lang_counts": lang,
    "rights_counts": rights,
    "ledger_status": Counter([r.get("status") for r in ledger]),
    "failed": [r["source_id"] for r in ledger if r.get("status") == "FAILED"],
    "accepted": [r["source_id"] for r in ledger if r.get("status") in {"DOWNLOADED", "VERIFIED_EXISTING"}],
    "approved_work_count": prov.get("approved_work_count"),
    "raw_checksum_sources": sorted(list((set(raw.keys()) if isinstance(raw, dict) else {r["source_id"] for r in raw}))),
    "clean_checksum_sources": sorted(list((set(cleancs.keys()) if isinstance(cleancs, dict) else {r["source_id"] for r in cleancs}))),
    "reserve_new_authors": len({e["author"] for e in reserve if e["author"] not in authors}),
    "reserve_new_entries": len([e for e in reserve if e["author"] not in authors]),
    "reserve_top_authors": Counter([e["author"] for e in reserve]).most_common(10),
}, indent=2))
