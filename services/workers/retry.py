from __future__ import annotations
import time
import math
from typing import Callable, Any

class ExponentialBackoffRetry:
    """Exponential backoff helper for worker job execution."""

    def __init__(self, base_delay: float = 0.5, max_delay: float = 10.0, backoff_factor: float = 2.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor

    def compute_delay(self, attempt: int) -> float:
        delay = self.base_delay * (self.backoff_factor ** (attempt - 1))
        return min(delay, self.max_delay)

    def execute_with_retry(self, fn: Callable[[], Any], max_attempts: int = 3) -> Any:
        last_exception = None
        for attempt in range(1, max_attempts + 1):
            try:
                return fn()
            except Exception as e:
                last_exception = e
                if attempt < max_attempts:
                    delay = self.compute_delay(attempt)
                    time.sleep(delay)
        raise last_exception
