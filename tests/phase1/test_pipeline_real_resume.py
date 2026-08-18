import unittest
import os
import json
import shutil
import subprocess
import sys
from pathlib import Path

class TestPipelineRealResume(unittest.TestCase):
    def setUp(self):
        # Setup temporary directories inside workspace
        self.workspace_tmp = Path(__file__).resolve().parent.parent.parent / "tmp_real_resume"
        if self.workspace_tmp.exists():
            shutil.rmtree(self.workspace_tmp)
        self.workspace_tmp.mkdir(parents=True, exist_ok=True)
        
        self.clean_dir = self.workspace_tmp / "clean"
        self.resume_dir = self.workspace_tmp / "resume"
        
        # Helper to create folders and mock raw documents
        for target_dir in [self.clean_dir, self.resume_dir]:
            raw_dir = target_dir / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            
            # Create subdirs
            for d in ["clean", "validated", "shards", "metadata", "manifest", "frozen"]:
                (target_dir / d).mkdir(parents=True, exist_ok=True)
                
            proposal_dir = target_dir / "proposals" / "pd5m_v7"
            proposal_dir.mkdir(parents=True, exist_ok=True)
            
            manifest_data = []
            for i in range(15):
                manifest_data.append({
                    "source_id": f"test_doc_{i}",
                    "title": f"Doc {i}",
                    "author": f"Author {i}",
                    "category": "FICTION"
                })
            with open(proposal_dir / "manifest.json", "w") as f:
                json.dump(manifest_data, f)
                
            for doc in manifest_data:
                sid = doc["source_id"]
                raw_text = (
                    "*** START OF THE PROJECT GUTENBERG EBOOK Mock ***\n"
                    f"Clean content for document {sid} repeated three times to have enough tokens!\n"
                    f"Clean content for document {sid} repeated three times to have enough tokens!\n"
                    "*** END OF THE PROJECT GUTENBERG EBOOK Mock ***\n"
                )
                with open(raw_dir / f"{sid}.txt", "w", encoding="utf-8") as f:
                    f.write(raw_text)

        # Write runner scripts
        self.script_part1 = self.workspace_tmp / "run_part1.py"
        self.script_part1.write_text(f"""
import sys
from pathlib import Path
sys.path.insert(0, r"{Path(__file__).resolve().parent.parent.parent}")
import dataset_pipeline

tmp_dir = Path(sys.argv[1])
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
""", encoding="utf-8")

        self.script_part2 = self.workspace_tmp / "run_part2.py"
        self.script_part2.write_text(f"""
import sys
from pathlib import Path
sys.path.insert(0, r"{Path(__file__).resolve().parent.parent.parent}")
import dataset_pipeline

tmp_dir = Path(sys.argv[1])
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

# Process 2 runs everything: completed stages (1-4) will skip, remaining (5-8) will execute
dataset_pipeline.stage_1_acquisition_and_stage_2_cleaning()
dataset_pipeline.stage_3_deduplication()
dataset_pipeline.stage_4_validation()
dataset_pipeline.stage_5_sharding()
dataset_pipeline.stage_6_metadata()
dataset_pipeline.stage_7_manifest()
dataset_pipeline.stage_8_freeze()
""", encoding="utf-8")

    def tearDown(self):
        if self.workspace_tmp.exists():
            shutil.rmtree(self.workspace_tmp)

    def test_cross_process_resume(self):
        # 1. RUN CLEAN PIPELINE COMPLETELY (Continuous reference run)
        res_clean = subprocess.run([
            sys.executable,
            str(self.script_part2),
            str(self.clean_dir)
        ], capture_output=True, text=True)
        self.assertEqual(res_clean.returncode, 0, f"Clean pipeline run failed: {res_clean.stderr}")

        # 2. RUN PROCESS 1 (Stops after stage 4 validation)
        res_p1 = subprocess.run([
            sys.executable,
            str(self.script_part1),
            str(self.resume_dir)
        ], capture_output=True, text=True)
        self.assertEqual(res_p1.returncode, 0, f"Process 1 run failed: {res_p1.stderr}")

        # Assert intermediate state is saved and sharding is not yet executed
        state_file = self.resume_dir / "pipeline_state.json"
        self.assertTrue(state_file.exists())
        with open(state_file, "r") as f:
            state_data = json.load(f)
        self.assertIn("VALIDATION", state_data["completed_stages"])
        self.assertNotIn("SHARDING", state_data["completed_stages"])
        self.assertFalse((self.resume_dir / "manifest" / "final_manifest.json").exists())

        # 3. RUN PROCESS 2 (Loads state, skips 1-4, completes 5-8)
        res_p2 = subprocess.run([
            sys.executable,
            str(self.script_part2),
            str(self.resume_dir)
        ], capture_output=True, text=True)
        self.assertEqual(res_p2.returncode, 0, f"Process 2 run failed: {res_p2.stderr}")

        # Assert final manifest exists in resume run
        final_manifest_resume = self.resume_dir / "manifest" / "final_manifest.json"
        self.assertTrue(final_manifest_resume.exists())

        # 4. Compare manifests between continuous clean run and cross-process resumed run
        with open(self.clean_dir / "manifest" / "final_manifest.json", "r") as f:
            manifest_clean = json.load(f)
        with open(final_manifest_resume, "r") as f:
            manifest_resume = json.load(f)

        self.assertEqual(manifest_clean, manifest_resume, "Manifest files diverged between continuous and resumed runs")

if __name__ == '__main__':
    unittest.main()
