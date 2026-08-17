import unittest
import os
import json
import shutil
import torch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "backend/models"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "backend/models/nexa_fm"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.models.nexa_fm.training_engine.dataloader import ShardDataLoader
from backend.models.nexa_fm.architecture import NexaFMModel
from backend.models.nexa_fm.config import NexaFMConfig
from dataset_pipeline import stage_5_sharding, stage_7_manifest, state, CLEAN_DIR, VALIDATED_DIR, SHARDS_DIR, MANIFEST_DIR

class TestCanonicalPipeline(unittest.TestCase):
    def setUp(self):
        state.state = {
            "completed_stages": [],
            "timestamps": {},
            "data": {}
        }
        for d in [CLEAN_DIR, VALIDATED_DIR, SHARDS_DIR, MANIFEST_DIR]:
            if d.exists():
                shutil.rmtree(d)
            d.mkdir(parents=True, exist_ok=True)
            
        self.doc_ids = ["test1", "test2", "test3", "test4", "test5"]
        for i, doc_id in enumerate(self.doc_ids):
            (CLEAN_DIR / f"{doc_id}.txt").write_text(f"Dummy content for {doc_id} repeated " * 10, encoding="utf-8")
            
        manifest = [{"source_id": doc_id, "title": f"Title {i}"} for i, doc_id in enumerate(self.doc_ids)]
        with open(VALIDATED_DIR / "validated_manifest.json", "w") as f:
            json.dump(manifest, f)
            
    def test_end_to_end_sharding_and_manifest(self):
        stage_5_sharding()
        
        self.assertTrue(state.is_completed("SHARDING"))
        self.assertTrue((SHARDS_DIR / "shard_manifest.json").exists())
        self.assertTrue((SHARDS_DIR / "train" / "shard_00000.bin").exists())
        
        with open(SHARDS_DIR / "shard_manifest.json", "r") as f:
            shard_manifest = json.load(f)
            self.assertTrue(len(shard_manifest) > 0)
            
        stage_7_manifest()
        
        self.assertTrue(state.is_completed("MANIFEST_CREATION"))
        self.assertTrue((MANIFEST_DIR / "final_manifest.json").exists())
        
        with open(MANIFEST_DIR / "final_manifest.json", "r") as f:
            final_manifest = json.load(f)
            
        self.assertEqual(final_manifest["dataset_name"], "NEXA")
        self.assertIn("dataset_version", final_manifest)
        self.assertNotEqual(final_manifest["content_hash"], "UNDEFINED")
        self.assertEqual(final_manifest["dataset_version"], f"1.0.0-{final_manifest['content_hash'][:8]}")

        loader = ShardDataLoader(str(SHARDS_DIR / "train"), batch_size=2, max_length=128)
        batch = next(iter(loader))
        self.assertEqual(batch.dtype, torch.long)
        self.assertEqual(batch.shape, (2, 128))
        
        config = NexaFMConfig(vocab_size=32000, max_context_length=128, hidden_size=128, num_layers=2, num_heads=4)
        model = NexaFMModel(config)
        logits = model(batch)
        self.assertEqual(logits.shape, (2, 128, 32000))

if __name__ == '__main__':
    unittest.main()
