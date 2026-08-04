import sys
import json
import os
import warnings

# Suppress tqdm and warnings
os.environ["TQDM_DISABLE"] = "1"
warnings.filterwarnings("ignore")

from rag_engine import RAGEngine
from document_parser import DocumentParser

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "File path required"}))
        sys.exit(1)
        
    file_path = sys.argv[1]
    
    try:
        # 1. Parse and extract text using OCR/PyPDF
        parser = DocumentParser()
        doc = parser.parse(file_path)
        
        # 2. Add to RAG Engine
        engine = RAGEngine()
        doc_id = engine.import_document(file_path, background=False)

        # 3. Add to Memory
        from memory_engine import MemoryEngine
        mem_engine = MemoryEngine()
        mem_content = f"User uploaded document {doc.get('file_name', '')}. Content snippet: {doc.get('content', '')[:1000]}"
        mem_engine.create_memory("vision_upload", mem_content)
        
        with engine.store._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM chunks WHERE doc_id = ?", (doc_id,))
            chunk_count = cursor.fetchone()[0]
            
        result = {
            "doc_id": doc_id,
            "file_name": doc["file_name"],
            "file_type": doc["file_type"],
            "chunk_count": chunk_count,
            "embedding_count": chunk_count,
            "extracted_text": doc.get("content", ""),
            "metadata": doc.get("metadata", {}),
            "message": "Upload & OCR successful"
        }
        
        # Output JSON with a special delimiter to avoid parsing stderr trash
        print("\n---JSON_RESULT_START---")
        print(json.dumps(result))
        print("---JSON_RESULT_END---")
    except Exception as e:
        print("\n---JSON_RESULT_START---")
        print(json.dumps({"error": str(e)}))
        print("---JSON_RESULT_END---")

if __name__ == "__main__":
    main()
