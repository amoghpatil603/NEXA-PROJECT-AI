import os
import json
import time
import hashlib
import hmac
import base64
import datetime

os.makedirs("nexa_security", exist_ok=True)

secrets_py = """
import os

class SecretManager:
    def __init__(self):
        self.jwt_secret = os.environ.get("NEXA_JWT_SECRET", "default_insecure_jwt_secret_change_me")
        self.api_secret = os.environ.get("NEXA_API_SECRET", "default_api_secret_key")
        self.db_pass = os.environ.get("NEXA_DB_PASS", "default_db_pass")
        self.encryption_key = os.environ.get("NEXA_ENCRYPTION_KEY", "default_enc_key")

    def get_jwt_secret(self):
        return self.jwt_secret
"""

auth_py = """
import hashlib
import hmac
import base64
import json
import time
from .secrets import SecretManager

class Authenticator:
    def __init__(self):
        self.secrets = SecretManager()
        self.users = {
            "admin": {"hash": self.hash_password("admin123"), "role": "Administrator"},
            "dev": {"hash": self.hash_password("dev123"), "role": "Developer"},
            "researcher": {"hash": self.hash_password("res123"), "role": "Researcher"},
            "user": {"hash": self.hash_password("user123"), "role": "Standard User"},
            "guest": {"hash": self.hash_password("guest123"), "role": "Guest"}
        }
        self.api_keys = {
            "sk-live-12345": "Developer",
            "sk-prod-99999": "Administrator"
        }

    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, username, password):
        user = self.users.get(username)
        if not user:
            return False
        return user["hash"] == self.hash_password(password)

    def generate_jwt(self, username):
        user = self.users.get(username)
        if not user:
            raise ValueError("User not found")
        
        header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip('=')
        payload = base64.urlsafe_b64encode(json.dumps({
            "sub": username,
            "role": user["role"],
            "exp": int(time.time()) + 3600,
            "iat": int(time.time())
        }).encode()).decode().rstrip('=')
        
        signature = base64.urlsafe_b64encode(
            hmac.new(self.secrets.get_jwt_secret().encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
        ).decode().rstrip('=')
        
        return f"{header}.{payload}.{signature}"
        
    def generate_refresh_token(self, username):
        return hashlib.sha256(f"{username}{time.time()}".encode()).hexdigest()

    def verify_jwt(self, token):
        try:
            header, payload, signature = token.split(".")
            expected_sig = base64.urlsafe_b64encode(
                hmac.new(self.secrets.get_jwt_secret().encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
            ).decode().rstrip('=')
            
            if not hmac.compare_digest(signature, expected_sig):
                return False, "Invalid signature"
                
            decoded_payload = json.loads(base64.urlsafe_b64decode(payload + "==").decode())
            if decoded_payload["exp"] < int(time.time()):
                return False, "Token expired"
                
            return True, decoded_payload
        except Exception as e:
            return False, str(e)
            
    def verify_api_key(self, api_key):
        return self.api_keys.get(api_key, None)
"""

rbac_py = """
class RBAC:
    def __init__(self):
        self.roles = {
            "Administrator": ["read", "write", "delete", "manage_users", "train_model", "deploy_model"],
            "Developer": ["read", "write", "train_model", "deploy_model"],
            "Researcher": ["read", "train_model"],
            "Standard User": ["read", "infer"],
            "Guest": ["read"]
        }

    def has_permission(self, role, action):
        return action in self.roles.get(role, [])
"""

rate_limit_py = """
import time

class RateLimiter:
    def __init__(self, limits=None):
        self.limits = limits or {
            "Administrator": 10000,
            "Developer": 5000,
            "Researcher": 1000,
            "Standard User": 100,
            "Guest": 10
        }
        self.usage = {}
        self.window = 60 # 60 seconds

    def check_limit(self, user_id, role):
        now = time.time()
        if user_id not in self.usage:
            self.usage[user_id] = []
            
        self.usage[user_id] = [t for t in self.usage[user_id] if now - t < self.window]
        
        limit = self.limits.get(role, 10)
        if len(self.usage[user_id]) >= limit:
            return False
            
        self.usage[user_id].append(now)
        return True
"""

audit_py = """
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
            f.write(json.dumps(entry) + "\\n")
        return entry
"""

with open("nexa_security/__init__.py", "w") as f:
    f.write("")
with open("nexa_security/secrets.py", "w") as f:
    f.write(secrets_py)
with open("nexa_security/auth.py", "w") as f:
    f.write(auth_py)
with open("nexa_security/rbac.py", "w") as f:
    f.write(rbac_py)
with open("nexa_security/rate_limit.py", "w") as f:
    f.write(rate_limit_py)
with open("nexa_security/audit.py", "w") as f:
    f.write(audit_py)
