import unittest
import argparse
from pathlib import Path
from scripts.train_pretrain import build_parser, create_pretraining_setup
from backend.models.model.config import NexaConfig
from backend.models.model.transformer import NexaTransformer
from backend.models.nexa_fm.training_engine.config import TrainingConfig

class TestPretrainEntrypoint(unittest.TestCase):
    def test_parser_defaults(self):
        parser = build_parser()
        args = parser.parse_args([])
        self.assertEqual(args.batch_size, 8)
        self.assertEqual(args.grad_accum, 4)
        self.assertEqual(args.lr, 3e-4)
        self.assertEqual(args.seed, 42)
        self.assertEqual(args.max_steps, 100000)

    def test_create_pretraining_setup(self):
        parser = build_parser()
        args = parser.parse_args(["--batch-size", "4", "--grad-accum", "2", "--max-steps", "500"])
        model, config, dataloader = create_pretraining_setup(args)
        
        self.assertIsInstance(model, NexaTransformer)
        self.assertIsInstance(config, TrainingConfig)
        self.assertEqual(config.batch_size, 4)
        self.assertEqual(config.gradient_accumulation_steps, 2)
        self.assertEqual(config.max_steps, 500)
        self.assertEqual(model.config.vocab_size, 8000)
        self.assertEqual(model.config.d_model, 512)

    def test_minimal_cpu_integration_dry_run(self):
        from backend.models.nexa_fm.training_engine.trainer import Trainer
        parser = build_parser()
        args = parser.parse_args(["--dry-run", "--batch-size", "2", "--dataset-dir", "data/shards"])
        model, config, dataloader = create_pretraining_setup(args)

        self.assertIsNotNone(dataloader)
        trainer = Trainer(model, config, dataloader)
        success = trainer.dry_run()
        self.assertTrue(success, "Dry run execution of Trainer forward/backward/step must succeed")

if __name__ == "__main__":
    unittest.main()
