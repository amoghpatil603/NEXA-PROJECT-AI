# Dataset Manager Guide

## Purpose
The Dataset Manager abstracts all file system interactions. The Training Engine and Dataset Pipeline **must never** interact with raw folders directly. They must request access exclusively through the Manager.

## Features
- **Auto-Discovery**: On startup, the manager scans `datasets/public` and `datasets/private`. Any manually dropped folders are automatically registered as `local_{folder_name}`.
- **Resilient Downloading**: Fetches remote datasets via the primary URL. If that fails, it cascades through mirrors. It supports byte-range resume headers for interrupted downloads.
- **Manifest Generation**: Generates JSON manifests capturing a snapshot of the dataset metadata and validation outcomes.

## Usage (Manual Datasets)
Due to licensing and bandwidth constraints, the primary method for populating NEXA is manual provisioning:
1. Obtain the dataset legally.
2. Place the uncompressed text files (TXT, JSON, JSONL, PDF) in `datasets/public/<dataset_name>/`.
3. Initialize the `DatasetManager()`. It will auto-discover and register the dataset.
4. Call `manager.verify_dataset("local_<dataset_name>")`.
5. Call `manager.get_dataset_path("local_<dataset_name>")` to feed the Dataset Pipeline.

## Usage (Remote Datasets)
```python
from backend.models.nexa_fm.dataset_manager import DatasetManager, DatasetRecord

manager = DatasetManager()
manager.register_dataset(DatasetRecord(
    dataset_id="open_web_text",
    display_name="Open Web Text",
    primary_source="https://example.com/dataset.jsonl",
    ...
))
manager.add_dataset("open_web_text") # Will attempt download
```
