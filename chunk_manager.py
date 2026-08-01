import uuid
from typing import List, Dict, Any

class ChunkManager:
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_document(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        content = document['content']
        doc_id = document['doc_id']
        file_path = document['file_path']
        file_name = document['file_name']
        
        chunks = []
        start = 0
        text_length = len(content)

        while start < text_length:
            end = start + self.chunk_size
            chunk_text = content[start:end]
            chunk_id = str(uuid.uuid4())
            
            chunks.append({
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "content": chunk_text,
                "metadata": {
                    "file_path": file_path,
                    "file_name": file_name,
                    "start_idx": start,
                    "end_idx": end
                },
                "embedding": []
            })
            
            start += (self.chunk_size - self.overlap)

        return chunks
