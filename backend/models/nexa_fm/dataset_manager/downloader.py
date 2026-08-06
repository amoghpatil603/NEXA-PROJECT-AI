import os
import hashlib
import time
import urllib.request
from urllib.error import URLError
from typing import Optional, List
from .models import DatasetRecord

class Downloader:
    def __init__(self, cache_dir: str = "datasets/cache"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def verify_checksum(self, filepath: str, expected_checksum: str) -> bool:
        if not expected_checksum:
            return True # Cannot verify
            
        sha256 = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                while True:
                    data = f.read(65536)
                    if not data:
                        break
                    sha256.update(data)
            return sha256.hexdigest() == expected_checksum
        except Exception:
            return False

    def download(self, dataset: DatasetRecord) -> bool:
        sources = [dataset.primary_source] + dataset.mirror_sources
        
        target_path = dataset.local_storage_path
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        for source in sources:
            if not source.startswith("http"):
                # E.g., manual path or local URI, skip actual download
                if os.path.exists(target_path):
                    return True
                continue
                
            try:
                print(f"Attempting to download {dataset.dataset_id} from {source}...")
                
                # Check for existing partial file for resume
                headers = {}
                mode = 'wb'
                initial_size = 0
                if os.path.exists(target_path):
                    initial_size = os.path.getsize(target_path)
                    if initial_size > 0:
                        headers['Range'] = f'bytes={initial_size}-'
                        mode = 'ab'
                
                req = urllib.request.Request(source, headers=headers)
                
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        with urllib.request.urlopen(req, timeout=10) as response, open(target_path, mode) as out_file:
                            while True:
                                data = response.read(65536)
                                if not data:
                                    break
                                out_file.write(data)
                        break # Success
                    except Exception as e:
                        print(f"Download attempt {attempt+1} failed: {e}")
                        time.sleep(2)
                
                if os.path.exists(target_path):
                    if self.verify_checksum(target_path, dataset.checksum):
                        return True
                    else:
                        print(f"Checksum mismatch for {dataset.dataset_id} from {source}.")
                        os.remove(target_path) # Remove invalid file
            except Exception as e:
                print(f"Failed to download from {source}: {e}")
                
        print(f"All sources failed for dataset {dataset.dataset_id}.")
        return False
