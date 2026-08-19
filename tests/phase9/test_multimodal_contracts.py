import unittest
from backend.vision.interfaces import ModalityType, ImageInput, AudioInput, MultimodalRequest

class TestMultimodalContracts(unittest.TestCase):
    def test_modality_types(self):
        self.assertEqual(ModalityType.TEXT, "text")
        self.assertEqual(ModalityType.IMAGE, "image")
        self.assertEqual(ModalityType.AUDIO, "audio")

    def test_valid_image_and_audio_inputs(self):
        img = ImageInput(mime_type="image/png", payload_ref="data/image.png", metadata={"width": 800})
        self.assertEqual(img.mime_type, "image/png")
        self.assertEqual(img.payload_ref, "data/image.png")

        aud = AudioInput(mime_type="audio/wav", payload_ref="data/audio.wav", metadata={"duration": 15.4})
        self.assertEqual(aud.mime_type, "audio/wav")
        self.assertEqual(aud.payload_ref, "data/audio.wav")

    def test_invalid_mime_types(self):
        with self.assertRaises(ValueError):
            ImageInput(mime_type="application/pdf", payload_ref="doc.pdf")
        with self.assertRaises(ValueError):
            ImageInput(mime_type="text/plain", payload_ref="doc.txt")
        with self.assertRaises(ValueError):
            AudioInput(mime_type="video/mp4", payload_ref="video.mp4")

    def test_empty_payload_references(self):
        with self.assertRaises(ValueError):
            ImageInput(mime_type="image/jpeg", payload_ref="")
        with self.assertRaises(ValueError):
            AudioInput(mime_type="audio/mp3", payload_ref="   ")

    def test_multimodal_request(self):
        img = ImageInput(mime_type="image/jpeg", payload_ref="img.jpg")
        aud = AudioInput(mime_type="audio/mp3", payload_ref="aud.mp3")
        req = MultimodalRequest(
            prompt="Analyze this chart and transcribe this audio",
            images=[img],
            audios=[aud]
        )
        self.assertEqual(req.prompt, "Analyze this chart and transcribe this audio")
        self.assertEqual(len(req.images), 1)
        self.assertEqual(len(req.audios), 1)

        with self.assertRaises(ValueError):
            MultimodalRequest(prompt="", images=[img])

    def test_unsupported_modality_rejection(self):
        with self.assertRaises(ValueError):
            MultimodalRequest(prompt=123)
        img = ImageInput(mime_type="image/jpeg", payload_ref="img.jpg")
        with self.assertRaises(ValueError):
            MultimodalRequest(prompt="Test prompt", images="not-a-list")
        with self.assertRaises(ValueError):
            MultimodalRequest(prompt="Test prompt", images=[img, "not-an-image-input"])
        with self.assertRaises(ValueError):
            MultimodalRequest(prompt="Test prompt", audios=["not-an-audio-input"])

    def test_multimodal_metadata_serialization(self):
        img = ImageInput(mime_type="image/png", payload_ref="img.png", metadata={"channels": 3})
        from dataclasses import asdict
        d = asdict(img)
        self.assertEqual(d["mime_type"], "image/png")
        self.assertEqual(d["metadata"]["channels"], 3)
        img2 = ImageInput(**d)
        self.assertEqual(img2.mime_type, img.mime_type)
        self.assertEqual(img2.metadata["channels"], 3)

if __name__ == "__main__":
    unittest.main()
