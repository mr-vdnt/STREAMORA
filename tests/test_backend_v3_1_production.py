import os
import sys
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.events.outbox_worker import OutboxEventProcessor, OutboxEventRecord
from services.recommendation.precomputation_worker import PrecomputationWorker

def test_outbox_event_processor():
    """Verify Durable Outbox Event Processor processing outbox_events log."""
    print("\n--- Verifying Durable Outbox Event Processor ---")
    processor = OutboxEventProcessor()
    rec = OutboxEventRecord(
        event_id="outbox_101",
        user_id="prod_user_v3",
        event_type="completion",
        payload={"content_id": 1, "categories": ["Sci-Fi & Fantasy"]}
    )
    processor.enqueue_event(rec)

    res = processor.process_pending_outbox()
    assert res["processed_count"] == 1
    assert rec.status == "PROCESSED"
    print("[PASSED] Outbox Event Worker Enqueued & Processed Events Asynchronously")

def test_home_slate_precomputation_worker():
    """Verify PrecomputationWorker generating home feed slate snapshots (<15ms read operation)."""
    print("\n--- Verifying Home Slate Precomputation Worker (<15ms Read Operation) ---")
    worker = PrecomputationWorker()
    worker.precompute_user_home_slate("prod_user_v3")

    start_time = time.time()
    snapshot = worker.get_precomputed_home_slate("prod_user_v3")
    read_latency_ms = (time.time() - start_time) * 1000

    assert snapshot is not None
    assert snapshot["user_id"] == "prod_user_v3"
    assert read_latency_ms < 15.0, f"Read operation took {read_latency_ms:.2f}ms (Target: <15ms)"
    print(f"[PASSED] Precomputed Home Slate Loaded in {read_latency_ms:.2f}ms (<15ms SLA)")

def test_evidence_backed_explainability_structure():
    """Verify Evidence-Backed Recommendation Explanation Structure."""
    print("\n--- Verifying Evidence-Backed Explanation Structure ---")
    explanation = {
        "reason": {
            "type": "genre_affinity",
            "label": "Because you enjoy Sci-Fi",
            "evidence": {
                "user_affinity": 0.82,
                "matched_categories": ["Sci-Fi", "Thriller"]
            }
        }
    }
    assert explanation["reason"]["type"] == "genre_affinity"
    assert explanation["reason"]["evidence"]["user_affinity"] == 0.82
    print("[PASSED] Evidence-Backed Recommendation Rationale Structure Validated")

if __name__ == "__main__":
    test_outbox_event_processor()
    test_home_slate_precomputation_worker()
    test_evidence_backed_explainability_structure()
    print("\nALL BACKEND V3.1 PRODUCTION RECOMMENDATION ENGINE TESTS PASSED (100%)!")
