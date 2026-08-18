import json
from dataset_validator import DatasetValidator
from pathlib import Path

validator = DatasetValidator()
clean_lines = []
with open("test_dataset.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        if not line.strip(): continue
        res = validator.validate_sample(line)
        if res["valid"]:
            clean_lines.append(line.strip())

with open("validated_dataset.jsonl", "w", encoding="utf-8") as f:
    f.write("\n".join(clean_lines) + "\n")

validator2 = DatasetValidator()
with open("validated_dataset.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        if not line.strip(): continue
        validator2.validate_sample(line)

report = validator2.generate_report()
with open("DATASET_VALIDATION_REPORT.md", "w") as f:
    f.write(report)

print("Validated dataset created.")
