import sys
with open('upload_runner.py', 'r') as f:
    code = f.read()

target = """        # 2. Add to RAG Engine
        engine = RAGEngine()
        doc_id = engine.import_document(file_path, background=False)"""

replacement = """        # 2. Add to RAG Engine
        engine = RAGEngine()
        doc_id = engine.import_document(file_path, background=False)

        # 3. Add to Memory
        from memory_engine import MemoryEngine
        mem_engine = MemoryEngine()
        mem_content = f"User uploaded document {doc.get('file_name', '')}. Content snippet: {doc.get('content', '')[:1000]}"
        mem_engine.create_memory("vision_upload", mem_content)"""

if target in code:
    code = code.replace(target, replacement)
    with open('upload_runner.py', 'w') as f:
        f.write(code)
    print("Patched upload_runner.py")
else:
    print("Target not found")
