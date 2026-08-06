import sys
content = open("backend/api/ai_service.py").read()

import re
# Replace vision endpoint
vision_match = re.search(r'    ocr_text = f"Processing image/document content from \{safe_filename\} in background\.\.\.".*?if rag_engine: None\n    }', content, re.DOTALL)
if vision_match:
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
    content = content.replace(vision_match.group(0), rep3)

# Replace voice endpoint
voice_match = re.search(r'@app\.post\("/voice"\).*?    \}', content, re.DOTALL)
if voice_match:
    rep4 = """@app.post("/voice")
async def voice(request: Request):
    return JSONResponse(status_code=501, content={"error": "Voice pipeline is not implemented (missing dependencies)."})"""
    content = content.replace(voice_match.group(0), rep4)

open("backend/api/ai_service.py", "w").write(content)
