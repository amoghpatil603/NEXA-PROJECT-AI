# Dataset Generation Audit

## Purpose

The purpose of this audit is to identify all dataset generation scripts currently in the repository and determine which ones to consolidate into a single canonical production pipeline.

## Analyzed Scripts

### 1. `run_r4_acquisition.py`

- **Purpose**: Automates the acquisition of text data from Project Gutenberg, cleans it, verifies integrity, calculates basic statistics, and generates metadata artifacts (e.g. `download_ledger.jsonl`, `clean_manifest.json`, `provenance.json`).
- **Input**: `data/proposals/pd5m_v7/manifest.json`, `data/proposals/pd5m_v7/artifact_integrity.json`
- **Output**: Raw texts in `data/recovery/raw`, cleaned texts in `data/recovery/clean`, metadata and ledger files in `data/acquisition/pd5m_v7`, report in `data/reports/phase_r4_final_report.md`.
- **Dependencies**: Built-in modules (os, json, hashlib, time, re, urllib, collections).

### 2. `generate_shards.py`

- **Purpose**: Reads cleaned text, tokenizes it using the production BPE tokenizer, and shards it into binary files for training, validation, and testing. It also checks dataset split integrity and generates shard manifests.
- **Input**: Cleaned texts in `data/recovery/clean`, `nexa-model/tokenizer/production/tokenizer.json`, `nexa-model/tokenizer/production/splits.json`
- **Output**: Binary shards in `data/shards/pd5m_v7_8k`, manifests (`shard_manifest.json`, `checksums.json`, `metadata.json`), reports in `data/reports`.
- **Dependencies**: Custom tokenizer (`nexa-model.tokenizer`), `array`, built-in modules.

### 3. Redundant / Experimental Scripts

Scripts such as `generate_shards_3f4t.py`, `generate_shards_3f4r.py`, `generate_shards_3f4tr.py`, `freeze_corpus.py`, `freeze_corpus-1.py`, `freeze_corpus-2.py`, `generate_final_report.py`, `generate_phase4b_reports.py` appear to be either redundant, intermediate experiments, or specialized one-off scripts.

## Canonical Pipeline Strategy

We will consolidate `run_r4_acquisition.py` (Acquisition, Cleaning, Deduplication, Validation) and `generate_shards.py` (Sharding, Metadata, Freeze) into a single deterministic, resumable pipeline orchestrated by `dataset_pipeline.py`.

The new canonical pipeline will maintain a state machine in `pipeline_state.json` to allow resumption upon interruption, and structure output artifacts cleanly.
