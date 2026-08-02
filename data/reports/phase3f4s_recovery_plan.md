NEXA PHASE 3F.4S — SAFE RECOVERY PLAN
=====================================

1. **Quarantine:** Move the corrupted shards from `data/shards/pd5m_v7_8k/` to a backup directory (e.g., `data/shards/corrupt_backup/`).
2. **Regeneration:** Re-run the known-good generator script (`generate_shards_3f4r.py`) to rebuild the shards from the clean text corpus.
3. **Verification:** Validate that the newly generated shards perfectly match the certified hashes previously recorded in `data/shards/pd5m_v7_8k/checksums.json` to guarantee bit-for-bit equivalence.
4. **Resumption:** Once verified, resume Phase 4B (Production Data Loader & Sequence Packing) using the restored shards.
