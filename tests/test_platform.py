import time
from services.platform.config.settings import settings
from services.platform.cache.cache_manager import CacheManager
from services.platform.monitoring.metrics import metrics_registry
from services.platform.resilience.circuit_breaker import circuit_breaker, CircuitBreakerOpenException
import pytest

def test_config():
    assert settings.ENV in ["development", "production", "test"]

def test_cache_manager():
    manager = CacheManager()
    
    # Store
    manager.set("query", "test_key", {"result": "success"}, ttl_seconds=60)
    
    # Retrieve
    val = manager.get("query", "test_key")
    assert val is not None
    assert val["result"] == "success"
    
    # Miss
    val_miss = manager.get("query", "invalid_key")
    assert val_miss is None
    
    metrics = manager.get_metrics()
    assert metrics["query"]["hits"] == 1
    assert metrics["query"]["misses"] == 1

def test_metrics_registry():
    metrics_registry.increment("test_counter", 2)
    metrics_registry.record_time("test_timer", 15.0)
    metrics_registry.record_time("test_timer", 25.0)
    
    snapshot = metrics_registry.get_snapshot()
    assert snapshot["counters"]["test_counter"] >= 2
    assert snapshot["timings_avg_ms"]["test_timer"] == 20.0

def test_circuit_breaker():
    call_count = 0
    
    @circuit_breaker(failure_threshold=2, recovery_timeout=1)
    def unstable_function():
        nonlocal call_count
        call_count += 1
        raise ValueError("Simulated Failure")
        
    # Call 1 (Fail)
    with pytest.raises(ValueError):
        unstable_function()
        
    # Call 2 (Fail) -> Circuit Opens
    with pytest.raises(ValueError):
        unstable_function()
        
    assert call_count == 2
    
    # Call 3 (Fail Fast)
    with pytest.raises(CircuitBreakerOpenException):
        unstable_function()
        
    assert call_count == 2 # Did not actually call the function
    
    # Wait for recovery
    time.sleep(1.1)
    
    # Call 4 (Half-Open)
    with pytest.raises(ValueError):
        unstable_function()
        
    assert call_count == 3
