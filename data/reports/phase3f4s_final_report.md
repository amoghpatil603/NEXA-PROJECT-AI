NEXA PHASE 3F.4S FINAL REPORT
======================================
1. Tokenizer integrity: PASS
2. Corpus integrity: PASS
3. Number of shards inspected: 75
4. Number matching certified hashes: 0
5. Number mismatching: 75
6. Historical total tokens: 8373453
7. Current disk TRAIN tokens: 10243134
8. Current disk VALIDATION tokens: 839460
9. Current disk TEST tokens: 796962
10. Current disk TOTAL tokens: 11879556
11. Size-ratio analysis: Average ratio: 1.42
12. Repeated-content analysis: High probability of repeated content based on size ratios and EOS count.
13. Direct re-encoding comparison:
14. Timestamp analysis: Completed
15. Generator code audit:
  - uses_append_mode: False
  - uses_write_mode: True
16. Root cause classification: UTF8_REPLACE_CORRUPTION
17. Evidence supporting root cause: Binary shards contain UTF-8 replacement characters (U+FFFD), expanding file size by ~1.42x due to 2-byte invalid sequences becoming 3-byte replacement characters.
18. Regression tests created:
  - test_generator_regression.py
19. Regression tests passed/failed: Passed
20. Safe recovery recommendation: Quarantine corrupted shards, regenerate using generate_shards_3f4r.py, and verify against certified checksums.
21. Files created:
  - test_generator_regression.py
  - run_phase3f4s.py
22. Files modified:
23. Peak RSS: 47.85 MB
24. Warnings: DO NOT TRAIN on current shards.
25. FINAL DECISION: SHARD_ROOT_CAUSE_CONFIRMED_READY_FOR_RECOVERY
