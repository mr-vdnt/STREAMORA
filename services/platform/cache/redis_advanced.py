import asyncio
import time
from typing import Optional, Any, Callable

class DistributedLock:
    """
    Async distributed lock abstraction for stampede prevention and task synchronization.
    """
    def __init__(self, name: str, timeout: int = 10):
        self.name = name
        self.timeout = timeout
        self._is_locked = False

    async def acquire(self) -> bool:
        # Simple async lock acquisition simulation
        self._is_locked = True
        return True

    async def release(self):
        self._is_locked = False

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.release()


class StampedePreventer:
    """
    Prevents cache stampedes using single-flight execution locks.
    """
    def __init__(self):
        self._locks: dict = {}

    async def fetch_or_compute(self, key: str, fetch_cache_fn: Callable, compute_fn: Callable, ttl: int = 300) -> Any:
        # Check cache first
        cached = await fetch_cache_fn(key) if asyncio.iscoroutinefunction(fetch_cache_fn) else fetch_cache_fn(key)
        if cached is not None:
            return cached

        # If cache miss, use single-flight lock
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()

        async with self._locks[key]:
            # Double check cache after acquiring lock
            cached = await fetch_cache_fn(key) if asyncio.iscoroutinefunction(fetch_cache_fn) else fetch_cache_fn(key)
            if cached is not None:
                return cached

            # Compute fresh result
            result = await compute_fn() if asyncio.iscoroutinefunction(compute_fn) else compute_fn()
            return result
