import os
import hashlib
from typing import Dict, Any

class DocumentParser:
    def __init__(self):
        self.supported_extensions = [
            '.pdf', '.txt', '.md', '.docx', '.csv', '.json',
            '.py', '.java', '.c', '.cpp', '.js', '.ts', '.html', '.css',
            '.png', '.jpg', '.jpeg', '.bmp', '.tiff'
        ]

    def parse(self, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        if ext not in self.supported_extensions:
            raise ValueError(f"Unsupported file type: {ext}")

        content = ""
        if ext == '.pdf':
            try:
                import pypdf
                with open(file_path, 'rb') as f:
                    reader = pypdf.PdfReader(f)
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            content += page_text + "\n"
                
                # Fallback to OCR if pypdf returns empty
                if not content.strip():
                    import pdfplumber
                    import pytesseract
                    with pdfplumber.open(file_path) as pdf:
                        for page in pdf.pages:
                            img = page.to_image()
                            text = pytesseract.image_to_string(img.original)
                            content += text + "\n"
            except ImportError as e:
                raise ImportError(f"Required pdf/ocr libraries not installed: {e}")
        elif ext == '.docx':
            try:
                import docx
                doc = docx.Document(file_path)
                content = "\n".join([para.text for para in doc.paragraphs])
            except ImportError as e:
                raise ImportError(f"python-docx not installed: {e}")
        elif ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
            try:
                import pytesseract
                from PIL import Image
                img = Image.open(file_path)
                content = pytesseract.image_to_string(img)
            except ImportError as e:
                raise ImportError(f"Required ocr libraries not installed: {e}")
        else:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError as e:
                raise ValueError(f"Binary or unsupported content format: {e}")

        file_name = os.path.basename(file_path)
        doc_id = hashlib.md5(file_path.encode('utf-8')).hexdigest()

        return {
            "doc_id": doc_id,
            "file_path": file_path,
            "file_name": file_name,
            "file_type": ext,
            "content": content,
            "metadata": {}
        }
