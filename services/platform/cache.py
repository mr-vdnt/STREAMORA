import json
import redis.asyncio as redis
from typing import Any, Optional, Callable
from functools import wraps
from core.config import get_settings

settings = get_settings()

class CacheManager:
    def __init__(self, url: str):
        self.redis = redis.from_url(url, decode_responses=True)
    
    async def get(self, namespace: str, key: str) -> Optional[Any]:
        full_key = f"{namespace}:{key}"
        data = await self.redis.get(full_key)
        if data:
            return json.loads(data)
        return None
        
    async def set(self, namespace: str, key: str, value: Any, expire_seconds: int = 3600):
        full_key = f"{namespace}:{key}"
        await self.redis.set(full_key, json.dumps(value), ex=expire_seconds)
        
    async def delete(self, namespace: str, key: str):
        full_key = f"{namespace}:{key}"
        await self.redis.delete(full_key)

    async def clear_namespace(self, namespace: str):
        # NOTE: Keys command is slow in production, but okay for targeted clears
        keys = await self.redis.keys(f"{namespace}:*")
        if keys:
            await self.redis.delete(*keys)

    async def close(self):
        await self.redis.close()

# Singleton cache instance
cache = CacheManager(settings.redis_url)

def cached(namespace: str, expire_seconds: int = 3600):
    """
    Decorator to cache the result of an async function in Redis.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate a simple key based on arguments
            key_parts = [str(arg) for arg in args] + [f"{k}={v}" for k, v in kwargs.items()]
            cache_key = ":".join(key_parts) if key_parts else "default"
            
            cached_result = await cache.get(namespace, cache_key)
            if cached_result is not None:
                return cached_result
                
            result = await func(*args, **kwargs)
            await cache.set(namespace, cache_key, result, expire_seconds)
            return result
        return wrapper
    return decorator
