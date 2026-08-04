import logging
import os
from datetime import datetime

class NexaLogger:
    def __init__(self, log_dir="/content/NEXA-PROJECT-AI/logs"):
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, f"inference_{datetime.now().strftime('%Y%m%d')}.log")
        
        self.logger = logging.getLogger("NexaInference")
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_file)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def log_inference(self, prompt, response, metrics):
        self.logger.info(f"PROMPT: {prompt}")
        self.logger.info(f"RESPONSE: {response}")
        self.logger.info(f"METRICS: {metrics}")
