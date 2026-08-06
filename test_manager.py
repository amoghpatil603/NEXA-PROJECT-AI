from backend.models.nexa_fm.dataset_manager import DatasetManager, DatasetRecord, DatasetStatus
import os
import json

def test_manager():
    # Setup dummy manual dataset
    os.makedirs("datasets/public/dummy_data", exist_ok=True)
    with open("datasets/public/dummy_data/data.jsonl", "w") as f:
        f.write(json.dumps({"text": "Hello world from manual dataset!"}) + "\n")
        f.write(json.dumps({"text": "Another line."}) + "\n")
        
    manager = DatasetManager()
    
    # Check if discovered
    discovered = manager.registry.get_dataset("local_dummy_data")
    assert discovered is not None
    assert discovered.status == DatasetStatus.DOWNLOADED
    
    # Verify dataset
    assert manager.verify_dataset("local_dummy_data") == True
    
    # Update metadata
    manager.update_metadata("local_dummy_data", description="Verified manual dataset")
    assert manager.registry.get_dataset("local_dummy_data").description == "Verified manual dataset"
    
    # Generate manifest
    manager.generate_manifest("local_dummy_data")
    assert os.path.exists("datasets/manifests/local_dummy_data_manifest.json")
    
    # Register external dataset
    ext_record = DatasetRecord(
        dataset_id="ext_wiki",
        display_name="Wiki Sample",
        description="A sample dataset",
        purpose="testing",
        license="MIT",
        languages=["en"],
        version="1.0",
        expected_size=100,
        local_storage_path="datasets/public/wiki_sample.txt",
        primary_source="https://raw.githubusercontent.com/invalid_url_for_test",
        mirror_sources=["https://another_invalid_url"]
    )
    manager.register_dataset(ext_record)
    
    # Try downloading (should fail gracefully)
    success = manager.add_dataset("ext_wiki")
    assert not success
    assert manager.registry.get_dataset("ext_wiki").status == DatasetStatus.FAILED
    
    print("Dataset Manager validation passed.")

if __name__ == "__main__":
    test_manager()
