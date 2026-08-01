from ocr_engine import OCREngine

class ImagePipeline:
    def __init__(self):
        self.ocr_engine = OCREngine()

    def process_image(self, image_path):
        # Pre-processing, OCR, Metadata Extraction
        text = self.ocr_engine.extract_text(image_path)
        return {
            "image_path": image_path,
            "extracted_text": text,
            "metadata": {"format": "png"}
        }
