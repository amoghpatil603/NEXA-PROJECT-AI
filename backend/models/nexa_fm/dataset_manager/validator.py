import os
import json
from typing import Dict, Any, List
from .models import DatasetRecord

class DatasetValidator:
    def __init__(self):
        pass

    def validate(self, dataset: DatasetRecord) -> Dict[str, Any]:
        report = {
            "dataset_id": dataset.dataset_id,
            "status": "VALID",
            "issues": [],
            "stats": {
                "total_files": 0,
                "empty_files": 0,
                "corrupted_files": 0,
            }
        }
        
        target_path = dataset.local_storage_path
        if not os.path.exists(target_path):
            report["status"] = "INVALID"
            report["issues"].append("Path does not exist")
            return report
            
        if os.path.isfile(target_path):
            files = [target_path]
        else:
            files = []
            for root, _, fnames in os.walk(target_path):
                for f in fnames:
                    files.append(os.path.join(root, f))
                    
        report["stats"]["total_files"] = len(files)
        
        for f in files:
            try:
                size = os.path.getsize(f)
                if size == 0:
                    report["stats"]["empty_files"] += 1
                    report["issues"].append(f"Empty file: {f}")
                
                # Check extension and try parsing if json/jsonl
                ext = os.path.splitext(f)[1].lower()
                if ext == '.json':
                    with open(f, 'r', encoding='utf-8') as file_obj:
                        json.load(file_obj)
                elif ext == '.jsonl':
                    with open(f, 'r', encoding='utf-8') as file_obj:
                        for line in file_obj:
                            if line.strip():
                                json.loads(line)
                                break # just test first line
            except Exception as e:
                report["stats"]["corrupted_files"] += 1
                report["issues"].append(f"Corrupted or unreadable file {f}: {e}")
                
        if report["stats"]["empty_files"] > 0 or report["stats"]["corrupted_files"] > 0:
            report["status"] = "HAS_ISSUES"
            
        return report
