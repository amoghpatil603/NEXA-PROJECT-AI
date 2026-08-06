import logging

logger = logging.getLogger(__name__)

class OCREngine:
    def __init__(self, language="eng"):
        self.language = language

    def extract_text(self, image_path):
        try:
            from PIL import Image
            import pytesseract
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, lang=self.language)
            return text
        except Exception as e:
            logger.error(f"OCR extraction failed for {image_path}: {e}")
            raise RuntimeError(f"OCR extraction failed: {e}")
