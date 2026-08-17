import unittest
import os
import json
import shutil
from pathlib import Path
import sys
import copy

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "backend/models"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "backend/models/nexa_fm"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from dataset_pipeline import stage_5_sharding, stage_7_manifest, state, CLEAN_DIR, VALIDATED_DIR, SHARDS_DIR, MANIFEST_DIR

class TestPipelineResume(unittest.TestCase):
    def setUp(self):
        for d in [CLEAN_DIR, VALIDATED_DIR, SHARDS_DIR, MANIFEST_DIR]:
            if d.exists():
                shutil.rmtree(d)
            d.mkdir(parents=True, exist_ok=True)
            
        self.doc_ids = ["test1", "test2", "test3"]
        for i, doc_id in enumerate(self.doc_ids):
            (CLEAN_DIR / f"{doc_id}.txt").write_text(f"Content {doc_id}", encoding="utf-8")
            
        self.manifest = [{"source_id": doc_id} for doc_id in self.doc_ids]
        with open(VALIDATED_DIR / "validated_manifest.json", "w") as f:
            json.dump(self.manifest, f)
            
    def test_resume_preserves_identity(self):
        state.state = {"completed_stages": [], "timestamps": {}, "data": {}}
        stage_5_sharding()
        stage_7_manifest()
        
        with open(MANIFEST_DIR / "final_manifest.json", "r") as f:
            manifest_a = json.load(f)
            
        for d in [SHARDS_DIR, MANIFEST_DIR]:
            if d.exists():
                shutil.rmtree(d)
            d.mkdir(parents=True, exist_ok=True)
            
        state.state = {"completed_stages": [], "timestamps": {}, "data": {}}
        stage_5_sharding()
        
        interrupted_state = copy.deepcopy(state.state)
        
        state.state = interrupted_state
        stage_7_manifest()
        
        with open(MANIFEST_DIR / "final_manifest.json", "r") as f:
            manifest_b = json.load(f)
            
        self.assertEqual(manifest_a["content_hash"], manifest_b["content_hash"])
        self.assertEqual(manifest_a["shard_count"], manifest_b["shard_count"])

if __name__ == '__main__':
    unittest.main()
