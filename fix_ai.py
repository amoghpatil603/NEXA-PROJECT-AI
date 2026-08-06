import sys

content = open("backend/api/ai_service.py").read()

target1 = """                else:
                    yield json.dumps({"chunk": "NEXA Response: Hello!", "full": "NEXA Response: Hello!", "time_taken": 0.05}) + "\\n\""""
rep1 = """                else:
                    yield json.dumps({"error": "501 Not Implemented: Chat engine models are missing."}) + "\\n\""""
content = content.replace(target1, rep1)

target2 = """            else:
                response_text = f"NEXA Response to: {message}\""""
rep2 = """            else:
                return JSONResponse(status_code=501, content={"error": "Chat engine models are missing."})"""
content = content.replace(target2, rep2)

target3 = """    ocr_text = f"Processing image/document content from {safe_filename} in background..."
    doc_id = "doc_1"
    if rag_engine:
        try:
            doc_id = rag_engine.import_document(file_path, background=True)
        except Exception as rag_err:
            logger.warning(f"RAGEngine warning: {rag_err}")

    return {
        "message": "Vision processed",
        "doc_id": doc_id,
        "ocr_text": ocr_text,
        "extracted_content": ocr_text,
        "filename": safe_filename,
        "job_id": doc_id if rag_engine else None
    }"""
rep3 = """    try:
        from backend.vision.image_pipeline import ImagePipeline
        pipeline = ImagePipeline()
        output = pipeline.process_image(file_path)
        ocr_text = output.get("extracted_text", "")
    except Exception as e:
        logger.error(f"OCR Pipeline failed: {e}")
        return JSONResponse(status_code=500, content={"error": f"OCR pipeline failed: {str(e)}"})

    doc_id = "doc_1"
    if rag_engine:
        try:
            doc_id = rag_engine.import_document(file_path, background=True)
        except Exception as rag_err:
            logger.error(f"RAGEngine error: {rag_err}")

    return {
        "message": "Vision processed",
        "doc_id": doc_id,
        "ocr_text": ocr_text,
        "extracted_content": ocr_text,
        "filename": safe_filename,
        "job_id": doc_id if rag_engine else None
    }"""
content = content.replace(target3, rep3)

target4 = """@app.post("/voice")
async def voice(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = {}
        
    text = data.get("text", "")
    if isinstance(text, str) and len(text) > 1000:
        text = text[:1000]

    return {
        "message": "Voice processed",
        "status": "ok",
        "transcript": text if text else "Voice input received successfully"
    }"""
rep4 = """@app.post("/voice")
async def voice(request: Request):
    return JSONResponse(status_code=501, content={"error": "Voice pipeline is not implemented (missing dependencies)."})"""
content = content.replace(target4, rep4)

open("backend/api/ai_service.py", "w").write(content)
