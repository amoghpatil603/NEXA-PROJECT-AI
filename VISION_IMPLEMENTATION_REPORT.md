# Vision Implementation Report

## Backend (Python)
- **DocumentParser**: Integrated OCR capabilities for multiple extensions. Uses `pypdf` for basic text extraction, and fails over to `pdfplumber` + `pytesseract` for scanned PDFs. Images directly hit `pytesseract` via `PIL`.
- **RAGEngine & VectorStore**: SQLite based storage for embedding-powered RAG using `sentence-transformers/all-MiniLM-L6-v2`.
- **upload_runner.py**: Executes parser, chunks the document, embeds it, and saves metadata into DB. Delivers a clean JSON response using protected output delimiters.

## Frontend (React/Vite)
- **VisionUploader.tsx**: Implements a floating interactive widget with state management for 'uploading', 'processing', 'success', and 'error'. Supports both Image/PDF types. 
- **ChatView.tsx**: Properly embeds VisionUploader into the chat input form for real-time document context insertion.

## API (Node/Express)
- **server.ts**: Implemented the `/api/upload` endpoint. Connects the frontend POST payload to the `.venv` activated Python script using Node `spawn`, and safely extracts JSON metadata.
