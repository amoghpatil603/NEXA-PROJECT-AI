import json
import os
from pathlib import Path

manifest_path = Path("data/proposals/pd5m_v7/manifest.json")
manifest_path.parent.mkdir(parents=True, exist_ok=True)
raw_dir = Path("data/recovery/raw")
raw_dir.mkdir(parents=True, exist_ok=True)

manifest = []

for i in range(1, 101):
    sid = f"instr_{i}"
    manifest.append({
        "source_id": sid,
        "title": f"Instruction {i}",
        "author": "Synthetic",
        "category": "INSTRUCTION",
        "work_id": f"W_{sid}"
    })
    text = f"Instruction: Solve problem {i}.\nOutput: Solution to problem {i}.\n"
    with open(raw_dir / f"{sid}.txt", "w") as f:
        f.write(text)

for i in range(1, 21):
    sid = f"pref_{i}"
    manifest.append({
        "source_id": sid,
        "title": f"Preference {i}",
        "author": "Synthetic",
        "category": "PREFERENCE",
        "work_id": f"W_{sid}"
    })
    text = f"Instruction: Problem {i}\nChosen: Good {i}\nRejected: Bad {i}\n"
    with open(raw_dir / f"{sid}.txt", "w") as f:
        f.write(text)

with open(manifest_path, "w") as f:
    json.dump(manifest, f, indent=2)

print(f"Generated {len(manifest)} synthetic samples.")
