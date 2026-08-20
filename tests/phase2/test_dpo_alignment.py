import unittest
import tempfile
import json
import os
import torch
from backend.models.nexa_fm.alignment.dpo_loss import compute_logprobs, compute_dpo_loss
from backend.models.nexa_fm.alignment.dpo_dataset import DPODataset
from scripts.train_dpo import build_parser

class TestDPOAlignment(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8")
        pairs = [
            {"prompt": "Hello", "chosen": "Hello! How can I assist?", "rejected": "Go away."},
            {"prompt": "2+2?", "chosen": "4", "rejected": "5"}
        ]
        for p in pairs:
            self.temp_file.write(json.dumps(p) + "\n")
        self.temp_file.close()

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_dpo_dataset_loading(self):
        dataset = DPODataset(self.temp_file.name)
        self.assertEqual(len(dataset), 2)
        
        def dummy_encode(text: str):
            return [ord(c) % 8000 for c in text]

        item = dataset.format_pair(dataset.pairs[0], dummy_encode)
        self.assertIn("chosen_input_ids", item)
        self.assertIn("rejected_input_ids", item)
        self.assertEqual(item["chosen_labels"][0].item(), -100)
        self.assertEqual(item["rejected_labels"][0].item(), -100)

    def test_dpo_loss_computation(self):
        # Policy favors chosen over rejected more than reference model
        policy_chosen = torch.tensor([-1.0, -2.0])
        policy_rejected = torch.tensor([-5.0, -6.0])
        ref_chosen = torch.tensor([-2.0, -3.0])
        ref_rejected = torch.tensor([-3.0, -4.0])

        loss, chosen_r, rejected_r = compute_dpo_loss(
            policy_chosen, policy_rejected, ref_chosen, ref_rejected, beta=0.1
        )
        self.assertIsInstance(loss, torch.Tensor)
        self.assertGreater(loss.item(), 0.0)
        # Chosen reward should exceed rejected reward
        self.assertTrue(torch.all(chosen_r > rejected_r))

    def test_compute_logprobs(self):
        # Fake logits (B=1, T=4, V=10)
        torch.manual_seed(42)
        logits = torch.randn(1, 4, 10)
        labels = torch.tensor([[1, 2, -100, 4]])
        logps = compute_logprobs(logits, labels)
        self.assertEqual(logps.shape, (1,))
        self.assertTrue(torch.isfinite(logps).item())

    def test_train_dpo_parser_defaults(self):
        parser = build_parser()
        args = parser.parse_args([])
        self.assertEqual(args.batch_size, 2)
        self.assertEqual(args.lr, 5e-6)
        self.assertEqual(args.beta, 0.1)
