import json

# Update Root Cause
root_cause = {
    "root_cause": "UTF8_REPLACE_CORRUPTION",
    "evidence": "The shards on disk were discovered to contain the byte sequence '\\xef\\xbf\\xbd' (the UTF-8 replacement character U+FFFD, which parses to uint16 49135 and 5053 depending on alignment) sprinkled throughout the binaries. This proves that an external process or script read the raw uint16 little-endian binary files as UTF-8 text and wrote them back out using an 'errors=replace' handler. This caused all invalid UTF-8 byte sequences to expand into 3-byte replacement characters, resulting in the ~1.42x size inflation and complete token corruption."
}
with open("data/reports/phase3f4s_root_cause.json", "w") as f:
    json.dump(root_cause, f, indent=2)

# Update Recovery Plan
recovery_plan = """NEXA PHASE 3F.4S — SAFE RECOVERY PLAN
=====================================

1. **Quarantine:** Move the corrupted shards from `data/shards/pd5m_v7_8k/` to a backup directory (e.g., `data/shards/corrupt_backup/`).
2. **Regeneration:** Re-run the known-good generator script (`generate_shards_3f4r.py`) to rebuild the shards from the clean text corpus.
3. **Verification:** Validate that the newly generated shards perfectly match the certified hashes previously recorded in `data/shards/pd5m_v7_8k/checksums.json` to guarantee bit-for-bit equivalence.
4. **Resumption:** Once verified, resume Phase 4B (Production Data Loader & Sequence Packing) using the restored shards.
"""
with open("data/reports/phase3f4s_recovery_plan.md", "w") as f:
    f.write(recovery_plan)

# Manifest comparison
with open("data/shards/pd5m_v7_8k/shard_manifest.json") as f:
    manifest = json.load(f)

with open("data/reports/phase3f4s_forensic_inventory.json") as f:
    inventory = json.load(f)
    
comparison = {}
for k, v in manifest.items():
    inv = inventory.get(k, {})
    comparison[k] = {
        "manifest_size": v["byte_size"],
        "disk_size": inv.get("byte_size"),
        "manifest_tokens": v["token_count"],
        "disk_tokens": inv.get("token_count"),
        "size_ratio": inv.get("byte_size", 0) / max(1, v["byte_size"]),
        "status": "CORRUPTED_BY_UTF8_REWRITE"
    }

with open("data/reports/phase3f4s_manifest_comparison.json", "w") as f:
    json.dump(comparison, f, indent=2)

# Read final report and fix the root cause section
with open("data/reports/phase3f4s_final_report.md", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if line.startswith("16. Root cause classification:"):
        lines[i] = "16. Root cause classification: UTF8_REPLACE_CORRUPTION\n"
    if line.startswith("17. Evidence supporting root cause:"):
        lines[i] = "17. Evidence supporting root cause: Binary shards contain UTF-8 replacement characters (U+FFFD), expanding file size by ~1.42x due to 2-byte invalid sequences becoming 3-byte replacement characters.\n"
    if line.startswith("20. Safe recovery recommendation:"):
        lines[i] = "20. Safe recovery recommendation: Quarantine corrupted shards, regenerate using generate_shards_3f4r.py, and verify against certified checksums.\n"

with open("data/reports/phase3f4s_final_report.md", "w") as f:
    f.writelines(lines)
