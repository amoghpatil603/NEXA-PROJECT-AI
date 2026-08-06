# Dataset Storage Layout

## Structure

```
datasets/
├── registry/
│   └── registry.json       # Central tracking file for all datasets
├── public/                 # Open-source, freely available raw datasets
├── private/                # Proprietary or licensed raw datasets
├── processed/              # Intermediary cleaned outputs (pre-sharding)
├── shards/                 # Final tokenized or pipeline-ready JSONL shards
├── metadata/               # Additional metadata, annotations, or schemas
├── manifests/              # Snapshot manifests of validated datasets
└── cache/                  # Temporary storage for interrupted downloads or archives
```

## Access Control
- `public/` and `private/` are the **Ingestion Zones**. Users can manually drop files here.
- `registry/` and `manifests/` are the **Control Zones**. Only the `DatasetManager` mutates these.
- `shards/` is the **Consumption Zone**. The Training Engine reads from here exclusively.
