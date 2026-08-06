import time
import logging
from enum import Enum

class RuntimeStatus(Enum):
    IDLE = "idle"
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"
    SHUTDOWN = "shutdown"

class RuntimeManager:
    """Manages the lifecycle of the NEXA Runtime."""
    def __init__(self):
        self.status = RuntimeStatus.IDLE
        self.start_time = None
        self.logger = logging.getLogger("NexaRuntime")

    def startup(self):
        self.status = RuntimeStatus.LOADING
        self.start_time = time.time()
        # Warm-up logic would go here
        self.status = RuntimeStatus.READY
        return {"status": "online", "uptime": self.get_uptime()}

    def shutdown(self):
        self.status = RuntimeStatus.SHUTDOWN
        return {"status": "offline"}

    def get_health(self):
        return {
            "status": self.status.value,
            "uptime": self.get_uptime() if self.start_time else 0,
            "healthy": self.status == RuntimeStatus.READY
        }

    def get_uptime(self):
        return time.time() - self.start_time if self.start_time else 0
