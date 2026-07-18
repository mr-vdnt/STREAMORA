import functools
import logging

logger = logging.getLogger("streamora.fallback")

def with_fallback(fallback_func):
    """Executes the fallback function if the main function raises an Exception."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Fallback triggered for {func.__name__} due to {e}")
                return fallback_func(*args, **kwargs)
        return wrapper
    return decorator
