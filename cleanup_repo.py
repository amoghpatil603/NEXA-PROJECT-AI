import os
import glob
import shutil

def cleanup():
    junk_patterns = [
        ",phase3e8b_*",
        ".phase3e8b_*",
        "acquire_reserve_work-*.py",
        "check_26225*",
        "check_selected*",
        "debug_evidence_root*",
        "diagnose_phase_3e8a*",
        "fix_*",
        "freeze_*",
        "generate_final_report*",
        "generate_phase4b_reports.py",
        "generate_shards*",
        "patch_*",
        "phase3*",
        "phase_3e8b_audit*",
        "run_*", # Be careful with this, but most are obsolete runners
        "temp_*",
        "test_*",
        "tmp_*"
    ]
    
    # Exclude important files that might match patterns
    exclude_files = [
        "run_full_training.py",
        "run_sft_pipeline.py",
        "start.sh",
        "prod_start.sh"
    ]
    
    files_to_remove = []
    for pattern in junk_patterns:
        files_to_remove.extend(glob.glob(pattern))
        
    for f in files_to_remove:
        if f in exclude_files:
            continue
        if os.path.isfile(f):
            print(f"Removing file: {f}")
            os.remove(f)
        elif os.path.isdir(f):
            print(f"Removing directory: {f}")
            shutil.rmtree(f)

if __name__ == "__main__":
    cleanup()
