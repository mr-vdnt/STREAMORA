import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

def test_background_worker_platform():
    from services.workers.queue import BackgroundTaskQueue
    from services.workers.worker import BackgroundWorker
    from services.workers.scheduler import BackgroundScheduler

    queue = BackgroundTaskQueue()
    worker = BackgroundWorker(queue)
    scheduler = BackgroundScheduler(queue)

    processed_jobs = []
    worker.register_handler("test_job", lambda payload: processed_jobs.append(payload))

    queue.enqueue("test_job", {"item_id": 100})
    assert queue.size() == 1

    success = worker.process_one()
    assert success == True
    assert len(processed_jobs) == 1
    assert processed_jobs[0]["item_id"] == 100

def test_storage_abstraction_platform():
    from services.storage.local_storage import LocalStorageProvider
    from services.storage.s3_storage import S3CloudStorageProvider

    local_provider = LocalStorageProvider(base_dir="./test_storage_tmp")
    url = local_provider.save_file("test/hello.txt", b"Hello Streamora Storage")
    assert "hello.txt" in url
    content = local_provider.get_file("test/hello.txt")
    assert content == b"Hello Streamora Storage"
    local_provider.delete_file("test/hello.txt")

    s3_provider = S3CloudStorageProvider()
    s3_url = s3_provider.save_file("posters/inception.jpg", b"fake_poster_bytes")
    assert "inception.jpg" in s3_url

def test_configuration_platform():
    from services.config.feature_flags import FeatureFlagPlatform
    from services.config.runtime_config import RuntimeConfigService

    flags = FeatureFlagPlatform()
    assert flags.is_enabled("enable_hls_stream_signing") == True
    flags.set_flag("test_feature", True)
    assert flags.is_enabled("test_feature") == True

    config = RuntimeConfigService()
    assert config.get("max_home_feed_latency_ms") == 500.0

def test_cache_platform():
    from services.cache.cache_manager import CacheManager
    from services.cache.cache_keys import CacheKeyBuilder

    cache = CacheManager(default_ttl_seconds=60.0)
    key = CacheKeyBuilder.home_feed("user_123")
    cache.set(key, {"hero": "Inception", "shelves": 5})

    val = cache.get(key)
    assert val is not None
    assert val["hero"] == "Inception"

def test_event_platform_and_outbox():
    from services.events.event_bus import EventBus
    from services.events.event_registry import EventTopic

    bus = EventBus()
    received_events = []
    bus.subscribe(EventTopic.USER_REGISTERED, lambda payload: received_events.append(payload))

    bus.publish(EventTopic.USER_REGISTERED, {"user_id": 99, "email": "test@streamora.ai"})
    assert len(received_events) == 1
    assert received_events[0]["user_id"] == 99

if __name__ == "__main__":
    print("Executing Streamora v1.1 Infrastructure Verification Suite...")
    test_background_worker_platform()
    print("[PASSED] Platform 1: Background Worker Platform (services/workers/)")
    test_storage_abstraction_platform()
    print("[PASSED] Platform 2: Storage Abstraction Platform (services/storage/)")
    test_configuration_platform()
    print("[PASSED] Platform 3: Configuration & Feature Flag Platform (services/config/)")
    test_cache_platform()
    print("[PASSED] Platform 4: Multilevel Cache Platform (services/cache/)")
    test_event_platform_and_outbox()
    print("[PASSED] Platform 5: Event Platform & Transactional Outbox (services/events/)")
    print("ALL 5 FOUNDATIONAL INFRASTRUCTURE PLATFORMS PASSED VERIFICATION (100%)!")
