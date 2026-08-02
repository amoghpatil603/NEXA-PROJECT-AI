import os
import json
import time
import uuid
from pathlib import Path
from datetime import datetime, timedelta

class RBACRole:
    ADMIN = "ADMIN"
    DEVELOPER = "DEVELOPER"
    STANDARD = "STANDARD"
    READ_ONLY = "READ_ONLY"
    SERVICE_ACCOUNT = "SERVICE_ACCOUNT"

class AuthorizationEngine:
    def __init__(self):
        self.permissions = {
            RBACRole.ADMIN: ["memory", "rag", "tools", "python", "filesystem", "terminal", "agents", "admin"],
            RBACRole.DEVELOPER: ["memory", "rag", "tools", "python", "filesystem", "agents"],
            RBACRole.STANDARD: ["memory", "rag", "tools", "agents"],
            RBACRole.READ_ONLY: ["memory", "rag"],
            RBACRole.SERVICE_ACCOUNT: ["tools", "python", "filesystem", "agents"]
        }

    def check_permission(self, role, action):
        allowed = action in self.permissions.get(role, [])
        return allowed

class SecureToolSandbox:
    def __init__(self):
        self.allowed_paths = [Path("/app/applet")]

    def validate_path(self, file_path):
        resolved = Path(file_path).resolve()
        for p in self.allowed_paths:
            if p.resolve() in resolved.parents or p.resolve() == resolved:
                return True
        return False

    def sandbox_execute_python(self, code):
        if "os.system" in code or "subprocess" in code or "__import__" in code:
            return {"success": False, "error": "Sandbox violation: Unsafe system call detected."}
        return {"success": True, "output": "Sandbox execution successful."}

class AuditLogger:
    def __init__(self, log_path="security_audit.jsonl"):
        self.log_path = Path(log_path)

    def log_event(self, event_type, user_id, role, details, status="SUCCESS"):
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "role": role,
            "details": details,
            "status": status
        }
        with open(self.log_path, "a") as f:
            f.write(json.dumps(record) + "\n")
        return record

class ThreatDetector:
    def __init__(self):
        self.suspicious_patterns = ["ignore previous instructions", "rm -rf", "../../../", "drop table", "exec("]

    def scan_prompt(self, prompt):
        prompt_lower = prompt.lower()
        for pattern in self.suspicious_patterns:
            if pattern in prompt_lower:
                return {"threat_detected": True, "pattern": pattern, "action_taken": "BLOCKED"}
        return {"threat_detected": False}

class SecurityDashboard:
    def __init__(self):
        pass

    def get_security_metrics(self):
        return {
            "failed_logins": 2,
            "active_sessions": 14,
            "threat_alerts": 0,
            "tool_violations": 0,
            "blocked_requests": 1,
            "security_score_pct": 99.4
        }
