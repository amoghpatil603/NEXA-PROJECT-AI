import sys
import json
from rag_engine import RAGEngine

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "File path required"}))
        sys.exit(1)
        
    file_path = sys.argv[1]
    engine = RAGEngine()
    
    try:
        doc_id = engine.import_document(file_path, background=False)
        stats = engine.store.get_stats()
        # Find how many chunks belong to this document
        with engine.store._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM chunks WHERE doc_id = ?", (doc_id,))
            chunk_count = cursor.fetchone()[0]
            
        print(json.dumps({
            "doc_id": doc_id,
            "chunk_count": chunk_count,
            "embedding_count": chunk_count,
            "message": "Upload successful"
        }))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    main()
