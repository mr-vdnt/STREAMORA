import time
import functools
import logging

logger = logging.getLogger("streamora.circuitbreaker")

class CircuitBreakerOpenException(Exception):
    pass

def circuit_breaker(failure_threshold: int = 3, recovery_timeout: int = 30):
    def decorator(func):
        # State associated with the function
        state = {
            "failures": 0,
            "last_failure_time": None,
            "state": "CLOSED" # CLOSED, OPEN, HALF-OPEN
        }
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            
            if state["state"] == "OPEN":
                if now - state["last_failure_time"] > recovery_timeout:
                    state["state"] = "HALF-OPEN"
                    logger.info(f"Circuit Breaker for {func.__name__} is HALF-OPEN")
                else:
                    raise CircuitBreakerOpenException(f"Circuit breaker is OPEN for {func.__name__}")
                    
            try:
                result = func(*args, **kwargs)
                # Success resets failure count
                if state["state"] == "HALF-OPEN":
                    state["state"] = "CLOSED"
                    logger.info(f"Circuit Breaker for {func.__name__} is CLOSED")
                state["failures"] = 0
                return result
            except Exception as e:
                if isinstance(e, CircuitBreakerOpenException):
                    raise
                
                state["failures"] += 1
                state["last_failure_time"] = time.time()
                
                if state["failures"] >= failure_threshold:
                    state["state"] = "OPEN"
                    logger.error(f"Circuit Breaker for {func.__name__} OPENED due to {e}")
                
                raise
        return wrapper
    return decorator
