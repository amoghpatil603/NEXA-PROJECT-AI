import os
import csv
import json
from pathlib import Path
from typing import Optional, Dict, Any

class MetricsLogger:
    """
    Multi-destination metrics logger supporting CSV, JSONL, and TensorBoard telemetry.
    """
    def __init__(
        self,
        output_dir: str | Path,
        csv_filename: str = "metrics.csv",
        jsonl_filename: str = "metrics.jsonl",
        tensorboard_dir: Optional[str] = "runs"
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.csv_path = self.output_dir / csv_filename
        self.jsonl_path = self.output_dir / jsonl_filename
        
        # Setup TensorBoard writer if available
        self.tb_writer = None
        if tensorboard_dir:
            tb_path = self.output_dir / tensorboard_dir
            try:
                from torch.utils.tensorboard import SummaryWriter
                self.tb_writer = SummaryWriter(log_dir=str(tb_path))
            except ImportError:
                self.tb_writer = None

    def log(self, metrics: Dict[str, Any]):
        """
        Logs a dictionary of metrics to CSV, JSONL, and TensorBoard.
        """
        # 1. Log to CSV
        file_exists = self.csv_path.exists()
        with open(self.csv_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(metrics.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(metrics)

        # 2. Log to JSONL
        with open(self.jsonl_path, mode="a", encoding="utf-8") as f:
            f.write(json.dumps(metrics) + "\n")

        # 3. Log to TensorBoard
        if self.tb_writer is not None and "global_step" in metrics:
            step = metrics["global_step"]
            for key, val in metrics.items():
                if key != "global_step" and isinstance(val, (int, float)):
                    self.tb_writer.add_scalar(key, val, global_step=step)

    def close(self):
        """
        Flushes and closes active loggers.
        """
        if self.tb_writer is not None:
            self.tb_writer.flush()
            self.tb_writer.close()
