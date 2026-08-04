from rag_engine import RAGEngine

rag = RAGEngine()
print("Importing README.md...")
try:
    rag.import_document("README.md")
    print("Imported successfully.")
except Exception as e:
    print(f"Import failed: {e}")

print("Searching for chunks...")
try:
    chunks = rag.store.search_chunks("README.md", top_k=3)
    print(f"Found {len(chunks)} chunks.")
    for c in chunks:
        print(c)
except Exception as e:
    print(f"Search failed: {e}")
