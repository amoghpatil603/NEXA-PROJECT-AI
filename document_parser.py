import os
import hashlib
from typing import Dict, Any

class DocumentParser:
    def __init__(self):
        self.supported_extensions = [
            '.pdf', '.txt', '.md', '.docx', '.csv', '.json',
            '.py', '.java', '.c', '.cpp', '.js', '.ts', '.html', '.css'
        ]

    def parse(self, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        _, ext = os.path.splitext(file_path)
        if ext.lower() not in self.supported_extensions:
            raise ValueError(f"Unsupported file type: {ext}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            content = "Binary or unsupported content format."

        file_name = os.path.basename(file_path)
        doc_id = hashlib.md5(file_path.encode('utf-8')).hexdigest()

        return {
            "doc_id": doc_id,
            "file_path": file_path,
            "file_name": file_name,
            "file_type": ext,
            "content": content
        }
