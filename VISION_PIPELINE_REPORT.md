# Vision Pipeline Report

## Execution Flow
1. **Frontend Request**: The React application sends FormData containing an image or PDF file to `/api/upload`.
2. **Express Backend**: `server.ts` receives the upload, stores it in the local `uploads` directory, and invokes a background Python subprocess targeting `upload_runner.py`.
3. **Document Parser**: Uses PyPDF and Tesseract OCR to extract string content from binary assets.
4. **Vector Knowledge Generation**: Text is chunked, embedded via the model, and injected into SQLite RAG index.
5. **Memory Formation**: An auxiliary summary string is passed to `MemoryEngine` ensuring that short and long-term conversation planners are aware of the newly uploaded document.
6. **Response Transport**: `server.ts` accurately slices `JSON_RESULT` barriers to return a successful parse notification.
