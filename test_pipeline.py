import os
from backend.models.nexa_fm.data_pipeline import DatasetPipeline

def test_pipeline():
    print("Running Dataset Pipeline Validation...")
    
    # We will use our own source code directory as a 'dataset' to validate the loaders!
    # This avoids fabricating training data while fully validating the pipeline logic.
    pipeline = DatasetPipeline(
        input_dir="backend/models/nexa_fm",
        output_dir="test_output_dataset",
        shard_size=10,
        min_length=10, # small min length to catch our source files
        allowed_languages=None # allow all for test
    )
    
    pipeline.run()
    
    print("Testing streaming...")
    count = 0
    for item in pipeline.stream_dataset():
        count += 1
        assert "text" in item
    
    print(f"Streamed {count} items successfully.")
    print("Validation passed.")

if __name__ == "__main__":
    test_pipeline()
