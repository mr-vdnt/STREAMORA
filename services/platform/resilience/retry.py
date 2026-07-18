import time
import functools
import logging

logger = logging.getLogger("streamora.retry")

def retry_with_backoff(retries=3, backoff_in_seconds=1, exceptions=(Exception,)):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if x == retries:
                        logger.error(f"Failed after {retries} retries: {e}")
                        raise
                    sleep = (backoff_in_seconds * 2 ** x)
                    logger.warning(f"Retrying {func.__name__} in {sleep}s due to {e}")
                    time.sleep(sleep)
                    x += 1
        return wrapper
    return decorator
