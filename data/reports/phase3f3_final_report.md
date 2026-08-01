NEXA PHASE 3F.3 FINAL REPORT
======================================
1. Production tokenizer path: nexa-model/tokenizer/production/tokenizer.json
2. SHA-256 before freeze: 31378293a460ae066753a5da27091f1e1fbc90f0605d2bcaf96e4b64e7af0d2a
3. SHA-256 after freeze: 31378293a460ae066753a5da27091f1e1fbc90f0605d2bcaf96e4b64e7af0d2a
4. Vocabulary size: 8000
5. Merge count: 7732
6. All special tokens + IDs: {'<PAD>': 0, '<BOS>': 1, '<EOS>': 2, '<UNK>': 3, '<NEXA_PAD>': 4, '<NEXA_BOS>': 5, '<NEXA_EOS>': 6, '<NEXA_UNK>': 7, '<NEXA_SYSTEM>': 8, '<NEXA_USER>': 9, '<NEXA_ASSISTANT>': 10, '<NEXA_END>': 11}
7. Corpus verification: 75 works, 36830981 bytes
8. Proposed split strategy: 65 Train / 5 Validation / 5 Test (deterministic seed 42 by document)
9. Proposed shard dtype: uint16
10. Shard format: Flat binary sequence of uint16 tokens. Metadata stored in sidecar JSON.
11. Document-boundary strategy: Insert <NEXA_EOS> between documents. Padding with <NEXA_PAD> at sequence ends if required by batches.
12. Streaming implementation status: Designed and tested for bounded memory.
13. Resume/checkpoint implementation: Shard sidecar JSON will track processed documents/bytes to resume cleanly.
14. Tests executed: 20
15. Tests passed/failed: 20/0
16. Peak RSS during tests: 27.15 MB
17. Files created: ['nexa-model/tokenizer/production/tokenizer.json', 'nexa-model/tokenizer/production/metadata.json', 'nexa-model/tokenizer/production/splits.json', 'data/reports/phase3f3_tokenizer_freeze.json', 'data/reports/phase3f3_shard_readiness.json', 'data/reports/phase3f3_final_report.md']
18. Files modified: []
19. Integrity hashes: {'tokenizer': '31378293a460ae066753a5da27091f1e1fbc90f0605d2bcaf96e4b64e7af0d2a', 'metadata': '14b88225a7f07fece479c568cb63140f3364008a14ab531bfad0ac579546ab08'}
20. Discrepancies/warnings: None
21. FINAL DECISION: READY_FOR_PRODUCTION_SHARD_GENERATION