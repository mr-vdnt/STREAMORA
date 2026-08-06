import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.recommendation.policy_config import RecommendationPolicy
from services.recommendation.evaluator import RecommendationEvaluator
from services.recommendation.recommendation_pipeline import RecommendationPipeline

def test_recommendation_policy_profiles():
    """Verify RecommendationPolicy dynamic weight configuration and profiles."""
    print("\n--- Verifying RecommendationPolicy Dynamic Profiles ---")
    p_default = RecommendationPolicy.get_preset_policy("default_balanced")
    assert p_default.franchise_weight == 0.35

    p_univ = RecommendationPolicy.get_preset_policy("universe_focused")
    assert p_univ.universe_weight == 0.35
    assert p_univ.franchise_weight == 0.25

    p_cast = RecommendationPolicy.get_preset_policy("cast_spotlight_focused")
    assert p_cast.cast_weight == 0.40
    print("[PASSED] Dynamic RecommendationPolicy Profiles Validated (default, universe, cast_spotlight)")

def test_recommendation_evaluator_metrics():
    """Verify offline IR evaluation metrics (Precision@K, Recall@K, NDCG@K, Catalog Coverage)."""
    print("\n--- Verifying Offline Recommendation Evaluator Metrics ---")
    rec_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    ground_truth = {1, 3, 5, 12, 15}

    prec = RecommendationEvaluator.precision_at_k(rec_ids, ground_truth, k=5)
    assert prec == 0.60, f"Precision@5 was {prec:.2f} (expected 0.60)"

    rec = RecommendationEvaluator.recall_at_k(rec_ids, ground_truth, k=5)
    assert rec == 0.60, f"Recall@5 was {rec:.2f} (expected 0.60)"

    ndcg = RecommendationEvaluator.ndcg_at_k(rec_ids, ground_truth, k=5)
    assert ndcg >= 0.60, f"NDCG@5 was {ndcg:.2f} (expected >= 0.60)"

    coverage = RecommendationEvaluator.catalog_coverage({1, 2, 3, 4, 5}, set(range(1, 21)))
    assert coverage == 25.0, f"Catalog coverage was {coverage:.1f}% (expected 25.0%)"

    print(f"[PASSED] Precision@5: {prec:.2f}")
    print(f"[PASSED] Recall@5: {rec:.2f}")
    print(f"[PASSED] NDCG@5: {ndcg:.2f}")
    print(f"[PASSED] Catalog Coverage: {coverage:.1f}%")

def test_recommendation_pipeline_with_policy():
    """Verify RecommendationPipeline instantiation with dynamic policy configuration."""
    print("\n--- Verifying RecommendationPipeline with Policy Configuration ---")
    p_univ = RecommendationPolicy.get_preset_policy("universe_focused")
    pipeline = RecommendationPipeline(policy=p_univ)
    assert pipeline.policy.universe_weight == 0.35
    print("[PASSED] RecommendationPipeline Policy Integration Validated")

if __name__ == "__main__":
    test_recommendation_policy_profiles()
    test_recommendation_evaluator_metrics()
    test_recommendation_pipeline_with_policy()
    print("\nALL RECOMMENDATION V3 HYBRID & EVALUATOR TESTS PASSED (100%)!")
