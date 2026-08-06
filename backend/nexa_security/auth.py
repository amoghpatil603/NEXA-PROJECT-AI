
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

    def hash_password(self, password: str, salt: bytes = b"nexa_secure_static_salt_v1") -> str:
        return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000).hex()

    def verify_password(self, username, password):
        user = self.users.get(username)
        if not user:
            return False
        computed = self.hash_password(password)
        return hmac.compare_digest(user["hash"], computed)

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
