import unittest
import os
import sys
import tempfile
import subprocess
import json

class TestFreshCheckoutIdentity(unittest.TestCase):
    def test_fresh_checkout_identity(self):
        # We write a clean python script that imports TrainingConfig and asserts fields are non-empty
        script_content = """
import sys
import json
from pathlib import Path

# Add the workspace root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.models.nexa_fm.training_engine.config import TrainingConfig

try:
    config = TrainingConfig()
    result = {
        "dataset_version": config.dataset_version,
        "dataset_content_hash": config.dataset_content_hash,
        "tokenizer_identity": config.tokenizer_identity,
        "tokenizer_config_identity": config.tokenizer_config_identity
    }
    print(json.dumps(result))
except Exception as e:
    import traceback
    print("ERROR:", str(e))
    traceback.print_exc()
    sys.exit(1)
"""
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write(script_content)
            temp_script = f.name

        try:
            # Run in a clean subprocess environment with PYTHONPATH set
            env = os.environ.copy()
            workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            env["PYTHONPATH"] = workspace_root
            
            res = subprocess.run(
                [sys.executable, temp_script],
                capture_output=True,
                text=True,
                env=env,
                cwd=workspace_root
            )
            self.assertEqual(res.returncode, 0, f"Subprocess failed with stderr:\n{res.stderr}\nstdout:\n{res.stdout}")
            
            # Parse output
            output = res.stdout.strip()
            self.assertTrue(output.startswith("{"), f"Unexpected output: {output}")
            data = json.loads(output)
            
            self.assertTrue(data["dataset_version"])
            self.assertTrue(data["dataset_content_hash"])
            self.assertTrue(data["tokenizer_identity"])
            self.assertTrue(data["tokenizer_config_identity"])
        finally:
            if os.path.exists(temp_script):
                os.remove(temp_script)

    def test_checkpoint_stores_all_four_values(self):
        # Verify that a checkpoint created using the current config stores all four values
        import torch
        import torch.nn as nn
        from backend.models.nexa_fm.training_engine.config import TrainingConfig
        from backend.models.nexa_fm.training_engine.checkpoints import CheckpointManager

        class TinyModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.l = nn.Linear(2, 2)
            def forward(self, x):
                return self.l(x)

        config = TrainingConfig(
            batch_size=1,
            gradient_accumulation_steps=1,
            max_steps=5,
            checkpoint_dir=tempfile.mkdtemp()
        )
        try:
            model = TinyModel()
            optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
            scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1)
            
            manager = CheckpointManager(config.checkpoint_dir)
            manager.save(
                model=model,
                optimizer=optimizer,
                scheduler=scheduler,
                step=1,
                micro_step=1,
                epoch=1,
                dataloader=None,
                config=config
            )
            
            state_file = os.path.join(config.checkpoint_dir, "checkpoint-1", "training_state.pt")
            self.assertTrue(os.path.exists(state_file))
            
            checkpoint = torch.load(state_file, map_location="cpu", weights_only=False)
            self.assertEqual(checkpoint.get("dataset_version"), config.dataset_version)
            self.assertEqual(checkpoint.get("dataset_content_hash"), config.dataset_content_hash)
            self.assertEqual(checkpoint.get("tokenizer_identity"), config.tokenizer_identity)
            self.assertEqual(checkpoint.get("tokenizer_config_identity"), config.tokenizer_config_identity)
        finally:
            import shutil
            shutil.rmtree(config.checkpoint_dir)

if __name__ == "__main__":
    unittest.main()
