import os
import json
import hashlib
from typing import List
from .registry import DatasetRegistry
from .models import DatasetRecord, DatasetStatus
from .downloader import Downloader
from .validator import DatasetValidator

class DatasetManager:
    def __init__(self, base_dir: str = "datasets"):
        self.base_dir = base_dir
        self.registry = DatasetRegistry(registry_dir=os.path.join(base_dir, "registry"))
        self.downloader = Downloader(cache_dir=os.path.join(base_dir, "cache"))
        self.validator = DatasetValidator()
        self.manifest_dir = os.path.join(base_dir, "manifests")
        os.makedirs(self.manifest_dir, exist_ok=True)
        
        self.discover_local_datasets()

    def discover_local_datasets(self):
        """Scans public and private folders to auto-register datasets."""
        dirs_to_scan = [os.path.join(self.base_dir, "public"), os.path.join(self.base_dir, "private")]
        for scan_dir in dirs_to_scan:
            if not os.path.exists(scan_dir):
                continue
            for item in os.listdir(scan_dir):
                item_path = os.path.join(scan_dir, item)
                dataset_id = f"local_{item}"
                if not self.registry.get_dataset(dataset_id):
                    # Auto register
                    size = 0
                    if os.path.isfile(item_path):
                        size = os.path.getsize(item_path)
                    else:
                        for r, _, f in os.walk(item_path):
                            for file in f:
                                size += os.path.getsize(os.path.join(r, file))
                    
                    record = DatasetRecord(
                        dataset_id=dataset_id,
                        display_name=item,
                        description="Automatically discovered local dataset.",
                        purpose="pre-training",
                        license="unknown",
                        languages=["en"],
                        version="1.0",
                        expected_size=size,
                        local_storage_path=item_path,
                        primary_source="local",
                        status=DatasetStatus.DOWNLOADED
                    )
                    self.registry.add_dataset(record)

    def register_dataset(self, record: DatasetRecord):
        self.registry.add_dataset(record)

    def add_dataset(self, dataset_id: str) -> bool:
        """Downloads or confirms existence of dataset."""
        record = self.registry.get_dataset(dataset_id)
        if not record:
            print(f"Dataset {dataset_id} not registered.")
            return False

        if os.path.exists(record.local_storage_path):
            self.registry.update_status(dataset_id, DatasetStatus.DOWNLOADED)
            return True

        success = self.downloader.download(record)
        if success:
            self.registry.update_status(dataset_id, DatasetStatus.DOWNLOADED)
        else:
            self.registry.update_status(dataset_id, DatasetStatus.FAILED)
        return success

    def remove_dataset(self, dataset_id: str):
        self.registry.remove_dataset(dataset_id)

    def verify_dataset(self, dataset_id: str) -> bool:
        record = self.registry.get_dataset(dataset_id)
        if not record:
            return False
            
        report = self.validator.validate(record)
        if report["status"] == "VALID":
            self.registry.update_status(dataset_id, DatasetStatus.VERIFIED)
            return True
        else:
            print(f"Validation failed for {dataset_id}: {report['issues']}")
            return False

    def update_metadata(self, dataset_id: str, **kwargs):
        record = self.registry.get_dataset(dataset_id)
        if record:
            for k, v in kwargs.items():
                if hasattr(record, k):
                    setattr(record, k, v)
            self.registry.save_registry()

    def generate_manifest(self, dataset_id: str):
        record = self.registry.get_dataset(dataset_id)
        if not record:
            return
            
        manifest_path = os.path.join(self.manifest_dir, f"{dataset_id}_manifest.json")
        report = self.validator.validate(record)
        
        manifest = {
            "dataset_info": record.to_dict(),
            "validation_report": report
        }
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)

    def get_dataset_path(self, dataset_id: str) -> str:
        """Pipeline Integration: Returns path only if downloaded/verified."""
        record = self.registry.get_dataset(dataset_id)
        if not record:
            raise ValueError(f"Dataset {dataset_id} not found.")
        if record.status not in [DatasetStatus.DOWNLOADED, DatasetStatus.VERIFIED, DatasetStatus.PROCESSED]:
            raise ValueError(f"Dataset {dataset_id} is not ready. Current status: {record.status}")
        return record.local_storage_path
