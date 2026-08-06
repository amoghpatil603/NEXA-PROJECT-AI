import os
import json
from typing import Dict, List, Optional
from .models import DatasetRecord, DatasetStatus

class DatasetRegistry:
    def __init__(self, registry_dir: str = "datasets/registry"):
        self.registry_dir = registry_dir
        self.registry_file = os.path.join(self.registry_dir, "registry.json")
        self.datasets: Dict[str, DatasetRecord] = {}
        os.makedirs(self.registry_dir, exist_ok=True)
        self.load_registry()

    def load_registry(self):
        if not os.path.exists(self.registry_file):
            self.datasets = {}
            return

        try:
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.datasets = {k: DatasetRecord.from_dict(v) for k, v in data.items()}
        except Exception as e:
            print(f"Error loading registry: {e}")
            self.datasets = {}

    def save_registry(self):
        try:
            data = {k: v.to_dict() for k, v in self.datasets.items()}
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving registry: {e}")

    def add_dataset(self, dataset: DatasetRecord):
        self.datasets[dataset.dataset_id] = dataset
        self.save_registry()

    def get_dataset(self, dataset_id: str) -> Optional[DatasetRecord]:
        return self.datasets.get(dataset_id)

    def remove_dataset(self, dataset_id: str):
        if dataset_id in self.datasets:
            del self.datasets[dataset_id]
            self.save_registry()

    def update_status(self, dataset_id: str, status: DatasetStatus):
        if dataset_id in self.datasets:
            self.datasets[dataset_id].status = status
            self.save_registry()
            
    def list_datasets(self) -> List[DatasetRecord]:
        return list(self.datasets.values())
