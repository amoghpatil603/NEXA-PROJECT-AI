import unittest
import os
import json
import shutil
import torch
import subprocess
import sys
from pathlib import Path

from backend.models.nexa_fm.training_engine.dataloader import ShardDataLoader
from backend.models.nexa_fm.architecture import NexaFMModel
from backend.models.nexa_fm.config import NexaFMConfig

class TestCanonicalE2EPipeline(unittest.TestCase):
    def setUp(self):
        # Setup temporary directories inside workspace
        self.tmp_dir = Path(__file__).resolve().parent.parent.parent / "tmp_canonical_e2e"
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

        # Create all pipeline directories in temp location
        for d in ["raw", "clean", "validated", "shards", "metadata", "manifest", "frozen"]:
            (self.tmp_dir / d).mkdir(parents=True, exist_ok=True)
        
        # Mock manifest.json in pd5m_v7
        proposal_dir = self.tmp_dir / "proposals" / "pd5m_v7"
        proposal_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate 15 documents to make sure train, validation, and test splits are all non-empty
        self.manifest_data = []
        for i in range(15):
            self.manifest_data.append({
                "source_id": f"test_doc_{i}",
                "title": f"Doc {i}",
                "author": f"Author {i}",
                "category": "FICTION" if i % 2 == 0 else "NON_FICTION"
            })
            
        with open(proposal_dir / "manifest.json", "w") as f:
            json.dump(self.manifest_data, f)
            
        # Write dummy raw text content with START/END markers to pass cleaning stage
        for doc in self.manifest_data:
            sid = doc["source_id"]
            raw_text = (
                "Header info\n"
                "*** START OF THE PROJECT GUTENBERG EBOOK Mock ***\n"
                f"This is the actual clean text content for document {sid} repeated three times to have enough tokens!\n"
                f"This is the actual clean text content for document {sid} repeated three times to have enough tokens!\n"
                "*** END OF THE PROJECT GUTENBERG EBOOK Mock ***\n"
                "Footer info\n"
            )
            with open(self.tmp_dir / "raw" / f"{sid}.txt", "w", encoding="utf-8") as f:
                f.write(raw_text)

        # Write execution script that runs all stages on the temp directory
        self.exec_script = self.workspace_root() / "tmp_canonical_e2e" / "run_e2e.py"
        self.exec_script.write_text(f"""
import sys
from pathlib import Path
sys.path.insert(0, r"{self.workspace_root()}")
import dataset_pipeline

tmp_dir = Path(r"{self.tmp_dir}")
dataset_pipeline.DATA_DIR = tmp_dir
dataset_pipeline.STATE_FILE = str(tmp_dir / "pipeline_state.json")
dataset_pipeline.RAW_DIR = tmp_dir / "raw"
dataset_pipeline.CLEAN_DIR = tmp_dir / "clean"
dataset_pipeline.VALIDATED_DIR = tmp_dir / "validated"
dataset_pipeline.SHARDS_DIR = tmp_dir / "shards"
dataset_pipeline.METADATA_DIR = tmp_dir / "metadata"
dataset_pipeline.MANIFEST_DIR = tmp_dir / "manifest"
dataset_pipeline.FROZEN_DIR = tmp_dir / "frozen"
dataset_pipeline.state = dataset_pipeline.PipelineState()

dataset_pipeline.stage_1_acquisition_and_stage_2_cleaning()
dataset_pipeline.stage_3_deduplication()
dataset_pipeline.stage_4_validation()
dataset_pipeline.stage_5_sharding()
dataset_pipeline.stage_6_metadata()
dataset_pipeline.stage_7_manifest()
dataset_pipeline.stage_8_freeze()
print("E2E_PIPELINE_COMPLETED_SUCCESSFULLY")
""", encoding="utf-8")

    def workspace_root(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent

    def tearDown(self):
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)

    def test_canonical_e2e_sequence(self):
        # 1. RUN THE INTEGRATION PIPELINE IN SUBPROCESS
        res = subprocess.run([
            sys.executable,
            str(self.exec_script)
        ], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Subprocess E2E pipeline run failed: {res.stderr}")
        self.assertIn("E2E_PIPELINE_COMPLETED_SUCCESSFULLY", res.stdout)

        # 2. VERIFY MANIFEST CREATED AND FOLLOWS THE SPEC
        final_manifest_path = self.tmp_dir / "manifest" / "final_manifest.json"
        self.assertTrue(final_manifest_path.exists())
        
        with open(final_manifest_path, "r") as f:
            final_manifest = json.load(f)
            
        self.assertEqual(final_manifest["dataset_name"], "NEXA")
        self.assertIn("dataset_version", final_manifest)
        self.assertTrue(final_manifest["dataset_version"].startswith("1.0.0-"))
        self.assertNotEqual(final_manifest["metadata"]["content_hash"], "UNDEFINED")
        self.assertEqual(final_manifest["train_documents"] + final_manifest["validation_documents"] + final_manifest["test_documents"], 15)

        # 3. VERIFY FREEZE INTEGRITY FILE CREATED
        self.assertTrue((self.tmp_dir / "frozen" / "integrity.json").exists())

        # 4. LOAD SHARDS USING REAL SHARDDATALOADER
        train_loader = ShardDataLoader(
            str(self.tmp_dir / "shards" / "train"),
            batch_size=1,
            max_length=8,
            shuffle=False
        )
        batches = list(train_loader)
        self.assertGreater(len(batches), 0)
        batch = batches[0]
        self.assertEqual(batch.dtype, torch.long)
        self.assertEqual(batch.shape[1], 8)

        # 5. PASS TO NEXAFMMODEL AND RUN FORWARD PASS
        config = NexaFMConfig(
            vocab_size=300,  # Authoritative v1 size
            max_context_length=8,
            hidden_size=64,
            num_layers=2,
            num_heads=2
        )
        model = NexaFMModel(config)
        model.eval()
        with torch.no_grad():
            logits = model(batch)
        self.assertEqual(logits.shape, (1, 8, 300))

if __name__ == '__main__':
    unittest.main()
