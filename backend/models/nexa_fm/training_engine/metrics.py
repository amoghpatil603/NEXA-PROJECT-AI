import json
import os
import time

class MetricsLogger:
    def __init__(self, log_dir: str):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, "training_log.jsonl")

    def log(self, metrics: dict):
        metrics['timestamp'] = time.time()
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(metrics) + "\n")
        
        # print to console
        print(f"Step {metrics.get('step')}: Loss {metrics.get('loss', 0):.4f} | LR {metrics.get('lr', 0):.2e}")
