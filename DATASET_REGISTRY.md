# Dataset Registry

## Overview
The NEXA Dataset Registry is the centralized tracking mechanism for all foundation model training data. It acts as the single source of truth for metadata, lineage, and processing state. 

## Dataset Record Schema
Every registered dataset contains the following metadata:
- `dataset_id`: Unique identifier (e.g., `local_books_corpus`).
- `display_name`: Human-readable name.
- `description`: Context about the dataset contents.
- `purpose`: Intended use (e.g., `pre-training`, `instruct-tuning`, `evaluation`).
- `license`: Usage rights (e.g., `MIT`, `CC-BY-4.0`, `Proprietary`).
- `languages`: List of ISO language codes (e.g., `["en", "es"]`).
- `version`: Dataset version.
- `expected_size`: Total byte size.
- `local_storage_path`: Where the raw files reside on disk.
- `primary_source`: URL or `local` designation for the dataset origin.
- `mirror_sources`: Fallback URLs for resilience.
- `checksum`: Expected SHA256 hash for integrity validation.
- `status`: Current state.

## States
1. `NOT_DOWNLOADED`: Registered but files are absent.
2. `DOWNLOADED`: Files reside on disk but haven't been integrity checked.
3. `VERIFIED`: Files passed validation (checksum, format, empty-checks).
4. `PROCESSED`: Filtered, cleaned, and sharded via the Dataset Pipeline.
5. `FAILED`: Download, validation, or processing failed.
