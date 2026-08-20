import unittest
import tempfile
import json
import os
import torch
from pathlib import Path
from backend.models.nexa_fm.sft.sft_dataset import SFTDataset
from scripts.train_sft import build_parser

class TestSFTPipeline(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8")
        sample_data = [
            {"prompt": "Hello!", "response": "Hi, how can I help you today?"},
            {"instruction": "Calculate 2+2", "output": "2 + 2 is 4."}
        ]
        for row in sample_data:
            self.temp_file.write(json.dumps(row) + "\n")
        self.temp_file.close()

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_sft_dataset_loading_and_formatting(self):
        dataset = SFTDataset(self.temp_file.name)
        self.assertEqual(len(dataset), 2)
        
        formatted = dataset.format_prompt_response("Hello!", "Hi there.")
        self.assertIn("<|im_start|>user", formatted["prompt"])
        self.assertIn("<|im_start|>assistant", formatted["prompt"])
        self.assertIn("Hi there.<|im_end|>", formatted["response"])

    def test_sft_loss_masking(self):
        dataset = SFTDataset(self.temp_file.name, max_seq_len=64)
        
        # Dummy encode function: char ordinal
        def dummy_encode(text: str):
            return [ord(c) % 8000 for c in text]

        processed = dataset.process_item_with_masking("Hi", "Hello world", dummy_encode)
        input_ids = processed["input_ids"]
        labels = processed["labels"]

        self.assertEqual(input_ids.shape, labels.shape)
        # Check that leading prompt tokens in labels are masked with -100
        self.assertEqual(labels[0].item(), -100)
        # Check that trailing assistant tokens are not -100
        self.assertNotEqual(labels[-1].item(), -100)

    def test_train_sft_parser_defaults(self):
        parser = build_parser()
        args = parser.parse_args([])
        self.assertEqual(args.batch_size, 4)
        self.assertEqual(args.lr, 2e-5)
        self.assertEqual(args.max_steps, 1500)
