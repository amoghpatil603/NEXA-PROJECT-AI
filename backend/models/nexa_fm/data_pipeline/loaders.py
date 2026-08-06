import os
import json
from typing import Iterator, Dict, Any

class DatasetLoader:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def scan_and_load(self) -> Iterator[Dict[str, Any]]:
        for dirpath, _, filenames in os.walk(self.root_dir):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                ext = os.path.splitext(filename)[1].lower()
                try:
                    if ext in ['.txt', '.md', '.py']:
                        yield from self._load_text(filepath)
                    elif ext == '.json':
                        yield from self._load_json(filepath)
                    elif ext == '.jsonl':
                        yield from self._load_jsonl(filepath)
                    elif ext == '.pdf':
                        yield from self._load_pdf(filepath)
                except Exception as e:
                    print(f"Error loading {filepath}: {e}")

    def _load_text(self, filepath: str) -> Iterator[Dict[str, Any]]:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if content.strip():
                yield {"text": content, "source": filepath}

    def _load_json(self, filepath: str) -> Iterator[Dict[str, Any]]:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and 'text' in item:
                        yield {"text": item['text'], "source": filepath, **item}
            elif isinstance(data, dict) and 'text' in data:
                yield {"text": data['text'], "source": filepath, **data}

    def _load_jsonl(self, filepath: str) -> Iterator[Dict[str, Any]]:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    if isinstance(item, dict) and 'text' in item:
                        yield {"text": item['text'], "source": filepath, **item}

    def _load_pdf(self, filepath: str) -> Iterator[Dict[str, Any]]:
        try:
            import PyPDF2
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                content = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        content.append(text)
                full_text = "\n".join(content)
                if full_text.strip():
                    yield {"text": full_text, "source": filepath}
        except ImportError:
            pass # PDF parsing requires PyPDF2
