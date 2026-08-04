
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
