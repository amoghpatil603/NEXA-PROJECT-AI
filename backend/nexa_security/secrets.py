
import os

class SecretManager:
    def __init__(self):
        self.jwt_secret = os.environ.get("NEXA_JWT_SECRET", "default_insecure_jwt_secret_change_me")
        self.api_secret = os.environ.get("NEXA_API_SECRET", "default_api_secret_key")
        self.db_pass = os.environ.get("NEXA_DB_PASS", "default_db_pass")
        self.encryption_key = os.environ.get("NEXA_ENCRYPTION_KEY", "default_enc_key")

    def get_jwt_secret(self):
        return self.jwt_secret
