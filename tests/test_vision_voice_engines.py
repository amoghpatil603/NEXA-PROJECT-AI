import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.vision.ocr_engine import OCREngine
from backend.vision.image_pipeline import ImagePipeline

class TestVisionVoiceEngines(unittest.TestCase):
    def test_ocr_engine_fails_missing_tesseract(self):
        ocr = OCREngine(language="eng")
        with self.assertRaises(RuntimeError):
            # Since pytesseract isn't installed in the test environment, this should raise
            result = ocr.extract_text("dummy/path/sample.png")

if __name__ == "__main__":
    unittest.main()
