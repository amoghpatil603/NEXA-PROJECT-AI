
import datetime
import json

class AuditLogger:
    def __init__(self, log_file="audit.log"):
        self.log_file = log_file

    def log(self, event_type, user, action, status, details=""):
        entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "event_type": event_type,
            "user": user,
            "action": action,
            "status": status,
            "details": details
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return entry
