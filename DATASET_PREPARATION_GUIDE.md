# Dataset Preparation Guide

## Supported Formats
- `.txt` / `.md`: Raw text. The entire file is treated as a single document.
- `.json` / `.jsonl`: Structured text. The pipeline expects a `"text"` key containing the document content. Other keys are preserved as metadata.
- `.pdf`: Processed for plain text extraction (requires `PyPDF2`).

## Legal & Ethical Requirements
**CRITICAL**: You must ONLY use datasets you have the legal right to use for training. 
- Do NOT upload copyrighted books without a license.
- Do NOT upload scraped website data if it violates the site's Terms of Service.
- Ensure personally identifiable information (PII) is removed *before* placing data into the pipeline input directories.

## Directory Structure
Place your legally sourced datasets in the `datasets/` directory (or any directory of your choosing), organized logically:

```
datasets/
├── code/
│   ├── open_source_repo_1.jsonl
│   └── permissively_licensed_snippets.txt
├── conversations/
│   └── synthetic_chat_dataset.json
└── wikipedia/
    └── cc_by_sa_articles.md
```

## Running the Pipeline
To execute the pipeline, instantiate the `DatasetPipeline` class from your training script:

```python
from backend.models.nexa_fm.data_pipeline import DatasetPipeline

pipeline = DatasetPipeline(
    input_dir="datasets/",
    output_dir="processed_shards/",
    shard_size=10000,
    min_length=100,       # Ignore very short snippets
    max_length=500000,    # Ignore excessively long documents
    allowed_languages=["en"] # Filter out non-English content
)

pipeline.run()
```

## Reviewing the Output
Once the pipeline finishes, review `processed_shards/report.json` to see how many documents were discarded and why (e.g., exact duplicates, failed language detection, insufficient length).
