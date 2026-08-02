# NEXA PROJECT RECOVERY STATUS

**Date:** July 29, 2026  
**Corpus Version Target:** NEXA-PD5M-v6.1  
**Target Accepted Works:** 84  
**Target Clean Bytes:** 58,404,307  
**Target Manifest SHA-256:** `ee075eb9683440c410a232bb50bbfc53e5a255d606ce199bdc6f8d75ae1ff193`  

---

## RECOVERY CATEGORIES
- **A. SURVIVING ORIGINAL FILE**: Original file surviving intact in workspace root.
- **B. RECONSTRUCTED FROM SPECIFICATION**: Code restored according to specifications. (Not byte-identical to lost originals).
- **C. REGENERATED DETERMINISTIC ARTIFACT**: Manifests/reports generated deterministically from verified sources.
- **D. MISSING / REQUIRES RECOVERY**: Lost artifact requiring reacquisition or code reconstruction.
- **E. VERIFIED AGAINST HISTORICAL HASH**: Reacquired file or manifest matching pre-loss hash.

---

## 1. PROJECT COMPONENT INVENTORY

### Desktop Application & Web Assets
| Component / File | Category | Status | Notes |
|---|---|---|---|
| `src/App.tsx` | A | SURVIVING ORIGINAL FILE | Frontend UI entry point |
| `src/main.tsx` | A | SURVIVING ORIGINAL FILE | React application mount |
| `src/index.css` | A | SURVIVING ORIGINAL FILE | Tailwind styles |
| `index.html` | A | SURVIVING ORIGINAL FILE | HTML container |
| `vite.config.ts` | A | SURVIVING ORIGINAL FILE | Vite configuration |
| `package.json` | A | SURVIVING ORIGINAL FILE | NPM dependencies |
| `tsconfig.json` | A | SURVIVING ORIGINAL FILE | TypeScript compiler options |
| `metadata.json` | A | SURVIVING ORIGINAL FILE | AI Studio Metadata (Name: NEXA) |
| `src-tauri/` | D | MISSING / REQUIRES RECOVERY | Local IPC & Tauri Rust application setup |

### Phase 3E / 3F Python Tools & Audit Artifacts (Root)
| Component / File | Category | Status | Notes |
|---|---|---|---|
| `phase3f1_train_and_benchmark.py` | A | SURVIVING ORIGINAL FILE | Tokenizer safety & benchmark preflight |
| `phase3f1_verify_and_explore.py` | A | SURVIVING ORIGINAL FILE | Tokenizer explorer & verification script |
| `generate_final_report.py` | A | SURVIVING ORIGINAL FILE | Corpus certification report generator |
| `freeze_corpus.py` | A | SURVIVING ORIGINAL FILE | Corpus metrics & manifest freezing tool |
| `acquire_reserve_work.py` | A | SURVIVING ORIGINAL FILE | Gutenberg acquisition & cleaning tool |
| `phase3e8c_execute_repair.py` | A | SURVIVING ORIGINAL FILE | Gutenberg reserve repair runner |
| `phase3e8c_post_repair.py` | A | SURVIVING ORIGINAL FILE | Post-repair validator |
| `phase_3e8b_audit.py` | A | SURVIVING ORIGINAL FILE | Corpus pre-repair audit script |
| `run_phase_3e8b_analysis.py` | A | SURVIVING ORIGINAL FILE | Concentration analysis runner |
| `run_phase_3e8b_search_combinations.py` | A | SURVIVING ORIGINAL FILE | Reserve combination search tool |
| `temp_manifest_sha.txt` | A | SURVIVING ORIGINAL FILE | Authoritative 84-work hash record |

### Reconstructed Core & Tokenizer Package (`nexa-model/`) — Phase R1
| Component / Path | Category | Status | Notes |
|---|---|---|---|
| `nexa-model/__init__.py` | B | RECONSTRUCTED FROM SPECIFICATION | Package root init |
| `nexa-model/tokenizer/__init__.py` | B | RECONSTRUCTED FROM SPECIFICATION | Tokenizer init |
| `nexa-model/tokenizer/bpe_tokenizer.py` | B | RECONSTRUCTED FROM SPECIFICATION | Reference `NexaBPETokenizer` (Byte BPE, deterministic tie-break, boundary protection) |
| `nexa-model/tokenizer/incremental_bpe.py` | B | RECONSTRUCTED FROM SPECIFICATION | `IncrementalBPETokenizer` (Incremental frequency tracking, 100% reference parity) |
| `nexa-model/tokenizer/train_bpe.py` | B | RECONSTRUCTED FROM SPECIFICATION | Tokenizer training orchestrator & CLI entry point |
| `nexa-model/data/__init__.py` | B | RECONSTRUCTED FROM SPECIFICATION | Data package init |
| `nexa-model/data/pipeline.py` | B | RECONSTRUCTED FROM SPECIFICATION | Document ingestion & streaming reader |
| `nexa-model/data/splits.py` | B | RECONSTRUCTED FROM SPECIFICATION | Train/val/test splitter with small-corpus protection |
| `nexa-model/data/sharding.py` | B | RECONSTRUCTED FROM SPECIFICATION | Binary uint32 token sharding and loader |
| `nexa-model/model/__init__.py` | B | RECONSTRUCTED FROM SPECIFICATION | Model package init |
| `nexa-model/training/__init__.py` | B | RECONSTRUCTED FROM SPECIFICATION | Training package init |
| `nexa-model/safety/__init__.py` | B | RECONSTRUCTED FROM SPECIFICATION | Safety package init |
| `nexa-model/inference/__init__.py` | B | RECONSTRUCTED FROM SPECIFICATION | Inference package init |
| `nexa-model/memory/__init__.py` | B | RECONSTRUCTED FROM SPECIFICATION | Local memory package init |
| `nexa-model/tests/__init__.py` | B | RECONSTRUCTED FROM SPECIFICATION | Test suite package init |
| `nexa-model/tests/test_tokenizer.py` | B | RECONSTRUCTED FROM SPECIFICATION | ASCII/Unicode, special token, save/load, error handling tests (8/8 PASS) |
| `nexa-model/tests/test_bpe_streaming.py` | B | RECONSTRUCTED FROM SPECIFICATION | Document boundary protection & streaming generator tests (2/2 PASS) |
| `nexa-model/tests/test_incremental_bpe.py` | B | RECONSTRUCTED FROM SPECIFICATION | Reference vs Incremental merge, vocab, encode/decode parity tests (3/3 PASS) |
| `nexa-model/tests/test_splits.py` | B | RECONSTRUCTED FROM SPECIFICATION | Small-corpus protection, seed determinism & binary sharding tests (6/6 PASS) |

### Remaining Missing Directories & Components
| Component / Path | Category | Status | Notes |
|---|---|---|---|
| `nexa-model/model/*` | D | MISSING / REQUIRES RECOVERY | Decoder-only Transformer implementation |
| `nexa-model/training/*` | D | MISSING / REQUIRES RECOVERY | Trainer, AdamW, checkpoint manager, metrics |
| `nexa-model/safety/*` | D | MISSING / REQUIRES RECOVERY | NEXA Constitution & security evaluation |
| `nexa-model/inference/*` | D | MISSING / REQUIRES RECOVERY | Local CPU/GPU runtime engine |
| `nexa-model/memory/*` | D | MISSING / REQUIRES RECOVERY | Local conversation persistence & RAG index |
| `nexa-model/data/clean/pd5m_v6/*.txt` | D | MISSING / REQUIRES RECOVERY | 84 clean text corpus files (58.4 MB) |

### Missing Data Manifests & Reports (`data/`)
| Component / Path | Category | Status | Notes |
|---|---|---|---|
| `data/acquisition/pd5m_v6/clean_manifest.json` | D | MISSING / REQUIRES RECOVERY | Master corpus manifest (84 works) |
| `data/acquisition/pd5m_v6/raw_checksums.json` | D | MISSING / REQUIRES RECOVERY | Raw file SHA-256 hashes |
| `data/acquisition/pd5m_v6/clean_checksums.json` | D | MISSING / REQUIRES RECOVERY | Clean file SHA-256 hashes |
| `data/acquisition/pd5m_v6/download_ledger.jsonl` | D | MISSING / REQUIRES RECOVERY | Provenance acquisition ledger |
| `data/proposals/pd5m_v6/reserve_repair_plan.json` | D | MISSING / REQUIRES RECOVERY | Repair sequence proposal |
| `data/reports/pd5m_v6_security_audit.json` | D | MISSING / REQUIRES RECOVERY | Security audit record |
| `data/reports/phase3f_resource_usage.jsonl` | D | MISSING / REQUIRES RECOVERY | Memory/CPU telemetry log |

### Missing Architecture Documentation (`docs/`)
| Component / Path | Category | Status | Notes |
|---|---|---|---|
| `docs/LOCAL_FIRST_ARCHITECTURE.md` | D | MISSING / REQUIRES RECOVERY | Local-first system specification |
| `docs/DATA_LIFECYCLE.md` | D | MISSING / REQUIRES RECOVERY | Client data deletion & storage lifecycle |
| `docs/SECURITY_ARCHITECTURE.md` | D | MISSING / REQUIRES RECOVERY | Safety constitution & tool boundaries |

---

## 2. RECONSTRUCTION & VERIFICATION SUMMARY

1. **Surviving Implementation Integrity**:
   - `phase3f1_train_and_benchmark.py` provides exact API contracts for `NexaBPETokenizer`, special tokens (`<PAD>`, `<BOS>`, `<EOS>`, `<UNK>`, `<NEXA_SYSTEM>`, `<NEXA_USER>`, `<NEXA_ASSISTANT>`), and safety memory limits (4 GB prestart gate, 1.5 GB hard abort).
   - `acquire_reserve_work.py` and `phase3e8c_execute_repair.py` provide exact deterministic Gutenberg cleaning rules (`clean_gutenberg_text`).

2. **Corpus Authority**:
   - Total certified works count: **84**.
   - Total certified clean bytes: **58,404,307**.
   - Final manifest SHA-256: `ee075eb9683440c410a232bb50bbfc53e5a255d606ce199bdc6f8d75ae1ff193`.
   - Work 26225 (`Fifteen Thousand Useful Phrases`) status: `FAILED_PRIMARY` (audio-only on Gutenberg).

3. **Current Container Environment Constraint**:
   - Total physical RAM: ~4.0 GB.
   - Available RAM: ~3.58 GB.
   - Requirement for Tokenizer Training: Prestart gate requires **>= 4.0 GB available RAM**.
   - Result: Heavy training is blocked in this container; unit testing and code reconstruction remain fully supported.
