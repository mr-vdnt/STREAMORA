import time
from typing import Dict, Tuple

class RateLimitExceeded(Exception):
    pass

class RateLimiter:
    """Simple sliding window rate limiter."""
    def __init__(self, requests_per_minute: int = 60):
        self.limit = requests_per_minute
        self.window = 60
        self.store: Dict[str, list] = {}
        
    def check_limit(self, user_id: str):
        now = time.time()
        
        if user_id not in self.store:
            self.store[user_id] = []
            
        # Clean up old entries
        self.store[user_id] = [t for t in self.store[user_id] if now - t < self.window]
        
        if len(self.store[user_id]) >= self.limit:
            raise RateLimitExceeded(f"Rate limit exceeded for user {user_id}. Try again later.")
            
        self.store[user_id].append(now)

# Global rate limiter
rate_limiter = RateLimiter()
