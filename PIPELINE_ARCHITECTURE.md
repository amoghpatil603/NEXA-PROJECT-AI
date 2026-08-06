# Pipeline Architecture

## Overview

The Canonical Dataset Generation Pipeline (`dataset_pipeline.py`) orchestrates the complete end-to-end data preparation process. It provides deterministic execution, structured logging, automatic resumption via state management, and clear stage separation.

## Stages

### 1. Data Acquisition
Downloads raw text data defined by the initial proposal manifest. Implements fallbacks and records download provenance in a ledger.

### 2. Cleaning
Strips headers/footers (e.g., Project Gutenberg boilerplates) and filters invalid texts deterministically. Output is saved to `data/clean/`.

### 3. Deduplication
Verifies that no two clean files have the same SHA-256 hash. Enforces strict uniqueness.

### 4. Validation
Checks for null bytes, HTML residue, executable signatures, and valid size bounds. Validates that the acquired texts meet all primary certification gates (e.g. unique authors, category distributions).

### 5. Sharding
Reads data based on canonical splits, tokenizes using the production tokenizer, and generates chunked binary shard files (`uint16`) capped at a maximum token size. Outputs to `data/shards/`.

### 6. Metadata Generation
Computes global dataset statistics, including token counts, boundaries, character lengths, and shard manifests.

### 7. Manifest Creation
Generates the final unified manifest containing checksums, sample counts, vocabulary mappings, domain distributions, and token estimates.

### 8. Freeze
Finalizes the pipeline by writing checksums for all output artifacts, marking the dataset version as immutable, and outputting the `DATASET_PIPELINE_REPORT.md`.

## Artifact Structure

```
data/
├── raw/             # Raw acquired texts
├── clean/           # Cleaned texts
├── validated/       # Checksums and security audit reports
├── shards/          # Binary .bin token shards
├── metadata/        # Distribution statistics and acquisition ledger
├── manifest/        # Final unified JSON manifest
└── frozen/          # Final integrity checksums
```

## State Management

The pipeline state is stored in `pipeline_state.json`.

```json
{
  "stages_completed": ["ACQUISITION", "CLEANING", "DEDUPLICATION"],
  "current_stage": "VALIDATION",
  "timestamps": {
    "ACQUISITION_start": "2024-01-01T00:00:00Z",
    "ACQUISITION_end": "2024-01-01T00:01:00Z"
  }
}
```

When started, `dataset_pipeline.py` reads this state and resumes from the first uncompleted stage.
