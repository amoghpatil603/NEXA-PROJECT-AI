import json
import os
from pathlib import Path
from datetime import datetime

class MemoryManager:
    def __init__(self, base_path='/content/NEXA-PROJECT-AI/nexa/memory'):
        self.base_path = Path(base_path)

    def _get_path(self, layer, identifier='default'):
        return self.base_path / layer / f'{identifier}.json'

    def save_memory(self, layer, data, identifier='default'):
        path = self._get_path(layer, identifier)
        record = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        with open(path, 'w') as f:
            json.dump(record, f, indent=2)
        return True

    def load_memory(self, layer, identifier='default'):
        path = self._get_path(layer, identifier)
        if not path.exists():
            return None
        with open(path, 'r') as f:
            return json.load(f)

    def search_memory(self, query, layer='long_term'):
        """Case-insensitive keyword search across JSON memory files."""
        path = self.base_path / layer
        results = []
        query_words = query.lower().split()
        if not path.exists():
            return results
            
        for file in path.glob('*.json'):
            try:
                with open(file, 'r') as f:
                    record = json.load(f)
                    content_str = str(record.get('data', '')).lower()
                    # Match if any significant keyword from the query is in the memory
                    if any(word in content_str for word in query_words if len(word) > 2):
                        results.append(record['data'])
            except Exception:
                continue
        return results
