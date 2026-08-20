import unittest
import tempfile
import shutil
import json
import torch
from pathlib import Path
from backend.models.model.config import NexaConfig
from backend.models.model.transformer import NexaTransformer
from backend.models.model.export import export_model_checkpoint
from scripts.export_model import build_parser

class TestModelExport(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_export_model_checkpoint(self):
        config = NexaConfig.tiny()
        model = NexaTransformer(config)

        res = export_model_checkpoint(model, config, self.test_dir, "custom_model.pt")
        
        self.assertTrue(Path(res["weights_path"]).exists())
        self.assertTrue(Path(res["config_path"]).exists())
        self.assertTrue(Path(res["manifest_path"]).exists())
        self.assertEqual(res["total_parameters"], 49721856)

        # Validate saved state dict
        loaded_state = torch.load(res["weights_path"], map_location="cpu", weights_only=True)
        self.assertIn("transformer.wte.weight", loaded_state)

        # Validate manifest
        with open(res["manifest_path"], "r", encoding="utf-8") as f:
            manifest = json.load(f)
        self.assertEqual(manifest["total_parameters"], 49721856)
        self.assertEqual(manifest["weights_file"], "custom_model.pt")

    def test_export_parser(self):
        parser = build_parser()
        args = parser.parse_args([])
        self.assertEqual(args.filename, "model.pt")
        self.assertEqual(args.output_dir, "exported_model")
