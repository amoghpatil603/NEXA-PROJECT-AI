# Dataset Pipeline Architecture

## Overview
The NEXA Dataset Pipeline is designed to process raw, legally sourced datasets into clean, deduplicated, and sharded formats suitable for foundation model training. It operates in a highly modular fashion, allowing for easy extensibility of loaders, cleaners, and filters.

## Components

1. **Loaders (`loaders.py`)**
   - Supports recursive directory traversal.
   - Extracts text from `.txt`, `.md`, `.json`, `.jsonl`, and `.pdf` files.
   - Designed to skip corrupted files without halting the entire pipeline.

2. **Cleaners (`cleaners.py`)**
   - **Unicode Normalization**: Applies NFKC normalization to handle varied character representations.
   - **Whitespace Cleanup**: Consolidates excessive spacing and newlines.
   - **HTML Removal**: Strips HTML tags using regex patterns.
   - **Control Characters**: Removes non-printable characters to prevent tokenization issues.

3. **Filters (`filters.py`)**
   - **Length Filter**: Discards documents that are too short (lacking context) or excessively long.
   - **Repetition Filter**: Uses n-gram and character repetition checks to discard spam or low-quality scraped data.
   - **Language Detection**: Configurable language filtering to focus training data (e.g., keeping only English or a curated set of languages). *Note: relies on `langdetect` if installed.*

4. **Deduplication (`dedup.py`)**
   - **Exact Deduplication**: Utilizes MD5 hashing on the normalized text to track and discard exact duplicates.
   - **Near Deduplication**: Supports MinHash/LSH (Locality-Sensitive Hashing) via `datasketch` for identifying documents with high overlap.

5. **Sharding & Streaming (`sharding.py`)**
   - Accumulates processed documents in a memory buffer.
   - Flushes to disk as numbered `.jsonl` shards (e.g., `shard_00001.jsonl`).
   - Provides a `stream_shards` generator to feed the training loop incrementally without OOM errors.
