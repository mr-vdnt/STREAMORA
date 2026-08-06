import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.recommendation.ann_index import HNSWVectorIndex
from services.recommendation.ltr_ranker import LearningToRankEngine, LTRFeatureVector
from services.recommendation.evaluator import RecommendationEvaluator
from services.recommendation.cold_start import ColdStartManager
from services.recommendation.observability import RetrievalObservabilityTracker

def test_hnsw_ann_vector_index():
    """Verify HNSW Approximate Nearest Neighbor vector search."""
    print("\n--- Verifying HNSW ANN Vector Search Index ---")
    index = HNSWVectorIndex(dimension=768)
    v1 = [0.1] * 768
    v2 = [0.1] * 768

    index.insert(1, v1)
    index.insert(2, v2)

    results = index.search_ann(v1, top_k=2)
    assert len(results) == 2
    assert results[0]["similarity"] > 0.99
    print(f"[PASSED] HNSW Sublinear Vector Search Similarity: {results[0]['similarity']:.4f}")

def test_ltr_feature_vector_ranker():
    """Verify Learning-to-Rank (LTR) Machine-Learned Feature Vector Ranker."""
    print("\n--- Verifying Learning-to-Rank (LTR) Engine ---")
    ltr = LearningToRankEngine()

    fv1 = LTRFeatureVector(content_id=1, graph_sim=0.90, vector_sim=0.85, popularity=80.0)
    fv2 = LTRFeatureVector(content_id=2, graph_sim=0.30, vector_sim=0.20, popularity=40.0)

    score1 = ltr.predict_score(fv1)
    score2 = ltr.predict_score(fv2)

    assert score1 > score2
    ranked = ltr.rank_candidates([fv1, fv2])
    assert ranked[0]["content_id"] == 1
    print(f"[PASSED] LTR Candidate #1 Score ({score1:.4f}) > Candidate #2 Score ({score2:.4f})")

def test_expanded_ir_evaluator_metrics():
    """Verify expanded IR evaluation metrics (MRR, MAP, HitRate@K)."""
    print("\n--- Verifying Expanded IR Evaluation Metrics (MRR, MAP, HitRate@K) ---")
    recs = [10, 1, 3, 5, 12]
    truth = {1, 3, 5}

    mrr = RecommendationEvaluator.mrr_at_k(recs, truth, k=5)
    hit_rate = RecommendationEvaluator.hit_rate_at_k(recs, truth, k=5)
    map_score = RecommendationEvaluator.map_at_k(recs, truth, k=5)

    assert mrr == 0.50, f"MRR was {mrr:.2f} (expected 0.50)"
    assert hit_rate == 1.0, f"HitRate was {hit_rate:.1f} (expected 1.0)"
    assert map_score > 0.40, f"MAP score was {map_score:.2f} (expected > 0.40)"

    print(f"[PASSED] MRR@5: {mrr:.2f}")
    print(f"[PASSED] HitRate@5: {hit_rate:.1f}")
    print(f"[PASSED] MAP@5: {map_score:.2f}")

def test_dual_cold_start_manager():
    """Verify Dual Cold-Start Strategy Execution."""
    print("\n--- Verifying Dual Cold-Start Strategy Engine ---")
    prior = ColdStartManager.get_new_title_cold_start_prior({"franchise": "Spider-Man", "universe": "MCU"})
    assert prior["initial_popularity_prior"] == 90.0
    assert prior["cold_start_status"] == "PROMOTED_NEW_RELEASE"
    print(f"[PASSED] Cold Start Popularity Prior for MCU Franchise Title: {prior['initial_popularity_prior']}")

def test_retrieval_observability_tracker():
    """Verify Retrieval Observability stage-level latency tracker."""
    print("\n--- Verifying Retrieval Observability Tracker ---")
    tracker = RetrievalObservabilityTracker()
    tracker.record_stage("vector_retrieval", 12.4)
    tracker.record_stage("graph_retrieval", 8.2)
    tracker.record_stage("ltr_ranking", 15.6)

    summary = tracker.get_summary()
    assert summary["vector_retrieval_ms"] == 12.4
    assert summary["graph_retrieval_ms"] == 8.2
    assert summary["ltr_ranking_ms"] == 15.6
    print(f"[PASSED] Stage Latency Breakdown: Vector ({summary['vector_retrieval_ms']}ms), Graph ({summary['graph_retrieval_ms']}ms), LTR ({summary['ltr_ranking_ms']}ms)")

if __name__ == "__main__":
    test_hnsw_ann_vector_index()
    test_ltr_feature_vector_ranker()
    test_expanded_ir_evaluator_metrics()
    test_dual_cold_start_manager()
    test_retrieval_observability_tracker()
    print("\nALL RECOMMENDATION V5 PRODUCTION SCALE TESTS PASSED (100%)!")
