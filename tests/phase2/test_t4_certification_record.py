import unittest
from pathlib import Path
from backend.models.model.config import NexaConfig
from backend.models.model.transformer import NexaTransformer

class TestT4CertificationRecord(unittest.TestCase):
    def setUp(self):
        self.doc_path = Path("docs/certification/PHASE_2B_T4_CERTIFICATION.md")

    def test_certification_document_exists(self):
        self.assertTrue(self.doc_path.exists(), "Phase 2B T4 Certification document must exist.")

    def test_certification_document_contents(self):
        content = self.doc_path.read_text(encoding="utf-8")
        
        required_strings = [
            "Phase 2B",
            "T4",
            "49,721,856",
            "0.0020",
            "checkpoint/resume",
            "31a17e56efe1372d694d28fc148f42b1985225d1"
        ]
        
        for req in required_strings:
            self.assertIn(req, content, f"Missing required evidence string '{req}' in certification document.")

        # Ensure closeout boundary clarity
        self.assertIn("NOT RE-RUN DURING THIS CLOSEOUT", content)
        self.assertIn("EXECUTED IN COLAB T4", content)

    def test_authoritative_tiny_config_architecture(self):
        cfg = NexaConfig.tiny()
        self.assertEqual(cfg.vocab_size, 8000)
        self.assertEqual(cfg.max_seq_len, 2048)
        self.assertEqual(cfg.d_model, 512)
        self.assertEqual(cfg.n_layers, 12)
        self.assertEqual(cfg.n_heads, 8)
        self.assertEqual(cfg.d_ff, 1792)
        self.assertTrue(cfg.weight_tying)
        self.assertEqual(cfg.pos_type, "rope")
        self.assertEqual(cfg.norm_type, "rmsnorm")

        # Static parameter count verification
        model = NexaTransformer(cfg)
        param_count = sum(p.numel() for p in model.parameters())
        self.assertEqual(param_count, 49721856, f"Expected 49,721,856 parameters, got {param_count}")
