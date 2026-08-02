import os
import csv
from pathlib import Path

class MetricsLogger:
    """
    CSV metrics logger for training telemetry.
    """
    def __init__(self, output_dir: str, filename: str = "metrics.csv"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.filepath = self.output_dir / filename
        self.initialized = self.filepath.exists()

    def log(self, metrics: dict):
        file_exists = self.filepath.exists()
        with open(self.filepath, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(metrics.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(metrics)
