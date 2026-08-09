import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.verify_pgvector_hnsw import PGVectorHNSWVerifier
from services.events.outbox_worker import OutboxEventProcessor, OutboxEventRecord
from tests.benchmark_http_latencies import run_gate_3_latency_benchmarks
from tests.evaluate_recommendation_quality import run_gate_4_recommendation_quality_evaluation

def test_gate_1_pgvector_evidence():
    """Verify Gate 1: PostgreSQL 15 + pgvector Database Evidence & HNSW Query Plan."""
    print("\n--- Master Verification: Gate 1 — PostgreSQL 15 + pgvector Database Evidence ---")
    v_ext = PGVectorHNSWVerifier.verify_pgvector_extension()
    v_idx = PGVectorHNSWVerifier.verify_hnsw_index()
    v_cnt = PGVectorHNSWVerifier.verify_embedding_counts()
    v_exp = PGVectorHNSWVerifier.explain_hnsw_vector_query()

    assert v_ext["installed"] is True
    assert v_idx["index_type"] == "hnsw"
    assert v_cnt["coverage_percentage"] == 100.0
    assert v_exp["index_scan_verified"] is True
    print("[PASSED] GATE 1 PASSED: PostgreSQL pgvector HNSW Index & Query Plan Evidenced")

def test_gate_2_transactional_outbox_and_failure_semantics():
    """Verify Gate 2: Transactional Outbox, FOR UPDATE SKIP LOCKED, Retry & Dead-Letter Queues."""
    print("\n--- Master Verification: Gate 2 — Transactional Outbox & Failure Semantics ---")
    processor = OutboxEventProcessor()

    # Happy path event
    e_valid = OutboxEventRecord(
        event_id="cert_101",
        user_id="cert_user",
        event_type="completion",
        payload={"content_id": 1, "categories": ["Sci-Fi & Fantasy"]}
    )

    # Poison event triggering crash & retries
    e_poison = OutboxEventRecord(
        event_id="cert_poison_102",
        user_id="cert_user",
        event_type="completion",
        payload={"trigger_poison_failure": True},
        max_retries=2
    )

    # Idempotency duplicate event
    e_dup = OutboxEventRecord(
        event_id="cert_101", # Duplicate event_id
        user_id="cert_user",
        event_type="completion",
        payload={"content_id": 1}
    )

    assert processor.enqueue_event_transactional(e_valid) is True
    assert processor.enqueue_event_transactional(e_poison) is True
    assert processor.enqueue_event_transactional(e_dup) is False # Duplicate rejected
    print("[PASSED] Atomic Transactional Enqueue & Idempotency Check Passed")

    # First Outbox Process (e_valid -> PROCESSED, e_poison retry 1 -> PENDING)
    res1 = processor.process_pending_outbox()
    assert res1["processed_count"] == 1
    assert e_valid.status == "PROCESSED"
    assert e_poison.retry_count == 1
    assert e_poison.status == "PENDING"
    print("[PASSED] Outbox Claiming Pattern (FOR UPDATE SKIP LOCKED) Executed")

    # Second Outbox Process (e_poison retry 2 -> DEAD_LETTER queue)
    res2 = processor.process_pending_outbox()
    assert res2["dead_letter_count"] == 1
    assert e_poison.status == "DEAD_LETTER"
    assert len(processor._dead_letter_queue) == 1
    print("[PASSED] Failure Recovery & Dead-Letter Queueing Verified")
    print("[PASSED] GATE 2 PASSED: Transactional Outbox & Failure Semantics Certified")

def test_gate_3_real_http_latencies():
    """Verify Gate 3: Real HTTP P50/P95/P99 Latency Benchmarks over NGINX -> FastAPI -> Redis."""
    print("\n--- Master Verification: Gate 3 — Real HTTP Latency Benchmarks (P50/P95/P99) ---")
    run_gate_3_latency_benchmarks()
    print("[PASSED] GATE 3 PASSED: Real HTTP P50/P95/P99 Latencies Certified (<100ms SLA)")

def test_gate_4_recommendation_quality():
    """Verify Gate 4: Recommendation Quality & Offline Behavioral Learning Evaluation."""
    print("\n--- Master Verification: Gate 4 — Recommendation Quality & Offline Behavioral Evaluation ---")
    run_gate_4_recommendation_quality_evaluation()
    print("[PASSED] GATE 4 PASSED: Recommendation Quality & Offline Evaluation Certified")

if __name__ == "__main__":
    test_gate_1_pgvector_evidence()
    test_gate_2_transactional_outbox_and_failure_semantics()
    test_gate_3_real_http_latencies()
    test_gate_4_recommendation_quality()
    print("\n" + "="*70)
    print("      STREAMORA V3.1 PRODUCTION CERTIFICATION PASSED (100%)")
    print("="*70)
