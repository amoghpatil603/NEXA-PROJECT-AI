import os
import json
from typing import Dict, Any, Iterator, List

class DatasetSharder:
    def __init__(self, output_dir: str, shard_size: int = 10000):
        self.output_dir = output_dir
        self.shard_size = shard_size
        self.current_shard = 0
        self.current_buffer = []
        os.makedirs(output_dir, exist_ok=True)

    def write(self, item: Dict[str, Any]):
        self.current_buffer.append(item)
        if len(self.current_buffer) >= self.shard_size:
            self._flush()

    def _flush(self):
        if not self.current_buffer:
            return
        
        shard_path = os.path.join(self.output_dir, f"shard_{self.current_shard:05d}.jsonl")
        with open(shard_path, 'w', encoding='utf-8') as f:
            for item in self.current_buffer:
                f.write(json.dumps(item) + "\n")
                
        self.current_buffer = []
        self.current_shard += 1

    def close(self):
        self._flush()

    @staticmethod
    def stream_shards(output_dir: str) -> Iterator[Dict[str, Any]]:
        if not os.path.exists(output_dir):
            return
            
        shard_files = sorted([f for f in os.listdir(output_dir) if f.endswith('.jsonl')])
        for shard_file in shard_files:
            shard_path = os.path.join(output_dir, shard_file)
            with open(shard_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        yield json.loads(line)
