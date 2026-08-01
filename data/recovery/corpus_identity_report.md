# NEXA PHASE R2 — CORPUS IDENTITY RECOVERY REPORT

**Date:** July 29, 2026  
**Corpus Target:** NEXA-PD5M-v6.1  
**Target Accepted Works:** 84  
**Target Clean Bytes:** 58,404,307  
**Target Manifest SHA-256:** `ee075eb9683440c410a232bb50bbfc53e5a255d606ce199bdc6f8d75ae1ff193`  

---

## 1. IDENTITY GATE STATUS

```
EXACT_IDENTITY_RECOVERED: FAIL
```

### Gate Assessment Summary
- **Positively Identified Works:** 10 / 84 works.
- **Unidentified Missing Works:** 74 / 84 works.
- **Acquisition Authorized:** NO (STOP condition triggered per Rule R2.3).

---

## 2. SURVIVING EVIDENCE AUDIT

Every surviving file, script, and artifact in the workspace was exhaustively inspected for evidence identifying the 84 certified Gutenberg works:

1. **`temp_manifest_sha.txt`**:
   - Confirms authoritative target metrics: 84 works, 58,404,307 clean bytes, manifest SHA-256 `ee075eb9683440c410a232bb50bbfc53e5a255d606ce199bdc6f8d75ae1ff193`.
   - Preserves 3 explicit clean SHA-256 file hashes:
     - `23.txt`: `dd486e6fbd229273d002d68cf02074947490337d7e5dcab3f9be1f44a7868c05`
     - `43453.txt`: `80d7622c4bfea508c163d22a0444fecefa07b07eb1eb365e49d33d867142f58`
     - `1564.txt`: `15ef8851545c38b1b1de788dc97d4f3f3170652c93b9c3a103184520f1bffc12`

2. **`phase3e8c_execute_repair.py` / `acquire_reserve_work.py` / `check_selected.py`**:
   - Confirms the 7 repair addition works added during Phase 3E.8C to reach the 84-work total:
     - Gutenberg ID `1837`: *The Prince and the Pauper* (Mark Twain)
     - Gutenberg ID `86`: *A Connecticut Yankee in King Arthur's Court* (Mark Twain)
     - Gutenberg ID `42188`: *Shadows in the Moonlight* (Robert E. Howard)
     - Gutenberg ID `42259`: *The People of the Black Circle* (Robert E. Howard)
     - Gutenberg ID `696`: *The Castle of Otranto* (Horace Walpole)
     - Gutenberg ID `121`: *Northanger Abbey* (Jane Austen)
     - Gutenberg ID `940`: *The Last of the Mohicans* (James Fenimore Cooper)

3. **`freeze_corpus.py` / `generate_final_report.py` / `phase3e8c_post_repair.py`**:
   - Confirms excluded / failed acquisition records:
     - `22962`: Failed acquisition
     - `26301`: Failed acquisition
     - `26225`: *Fifteen Thousand Useful Phrases* (FAILED_PRIMARY — audio-only on Gutenberg, no usable plain text)

4. **Missing Baseline Manifests (`data/acquisition/pd5m_v6/clean_manifest.json`)**:
   - The original baseline pre-repair corpus consisted of 77 works. The detailed `clean_manifest.json` containing the Gutenberg IDs, titles, authors, categories, and checksums for the remaining 74 baseline works was deleted prior to Phase R1 and is not embedded within any surviving python script.

---

## 3. POSITIVELY IDENTIFIED WORKS (10 / 84)

| Source ID | Title | Author | Category | Clean Hash / Source Evidence | Confidence |
|---|---|---|---|---|---|
| `1837` | The Prince and the Pauper | Mark Twain | FICTION | Gutenberg eBook 1837 | HIGH (Confirmed Addition) |
| `86` | A Connecticut Yankee in King Arthur's Court | Mark Twain | FICTION | Gutenberg eBook 86 | HIGH (Confirmed Addition) |
| `42188` | Shadows in the Moonlight | Robert E. Howard | FICTION | Gutenberg eBook 42188 | HIGH (Confirmed Addition) |
| `42259` | The People of the Black Circle | Robert E. Howard | FICTION | Gutenberg eBook 42259 | HIGH (Confirmed Addition) |
| `696` | The Castle of Otranto | Horace Walpole | FICTION | Gutenberg eBook 696 | HIGH (Confirmed Addition) |
| `121` | Northanger Abbey | Jane Austen | FICTION | Gutenberg eBook 121 | HIGH (Confirmed Addition) |
| `940` | The Last of the Mohicans | James Fenimore Cooper | FICTION | Gutenberg eBook 940 | HIGH (Confirmed Addition) |
| `23` | *Title unstated in surviving txt* | *Author unstated* | *Category unstated* | `dd486e6fbd229273d002d68cf0207494749...` | HIGH (Confirmed Hash) |
| `43453` | *Title unstated in surviving txt* | *Author unstated* | *Category unstated* | `80d7622c4bfea508c163d22a0444fecefa...` | HIGH (Confirmed Hash) |
| `1564` | *Title unstated in surviving txt* | *Author unstated* | *Category unstated* | `15ef8851545c38b1b1de788dc97d4f3f31...` | HIGH (Confirmed Hash) |

---

## 4. STOP CONDITION & RECOVERY CLASSIFICATION

Per **Rule R2.3**:
- Since the exact identity of all 84 works CANNOT be established (74 works remain unidentified):
  - **STOP**
  - **Classification:** `C — INCOMPLETE RECOVERY`
  - **Books Downloaded:** 0 (Acquisition strictly prohibited when gate = FAIL).

---

## 5. EXACT MISSING INFORMATION

To achieve `EXACT_IDENTITY_RECOVERED = PASS`, the following missing information is required:
1. The list of Gutenberg IDs, titles, and authors for the 74 unidentified baseline works.
2. Historical clean and raw SHA-256 hashes for the 74 baseline works (and historical raw hashes for the 7 repair works).
3. The exact provenance and category assignments for the baseline corpus.

---
