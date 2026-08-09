import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.recommendation.evaluator import RecommendationEvaluator
from services.events.telemetry_processor import PreferenceLearningEngine, TelemetryEventDTO

def run_gate_4_recommendation_quality_evaluation():
    print("\n--- Gate 4: Recommendation Quality & Behavioral Learning Evaluation ---")

    # 1. Evaluate Behavioral Event Weight Update Dynamics
    engine = PreferenceLearningEngine()
    events = [
        TelemetryEventDTO(event_id="e1", user_id="eval_user", event_type="click", categories=["Sci-Fi & Fantasy"]),
        TelemetryEventDTO(event_id="e2", user_id="eval_user", event_type="completion", categories=["Sci-Fi & Fantasy"]),
        TelemetryEventDTO(event_id="e3", user_id="eval_user", event_type="dislike", categories=["Romantic Movies"])
    ]
    engine.process_event_batch(events)
    profile = engine.get_user_preference_profile("eval_user")

    assert profile["Sci-Fi & Fantasy"] > 1.0, f"Sci-Fi weight was {profile['Sci-Fi & Fantasy']} (expected > 1.0)"
    assert profile["Romantic Movies"] < 0.0, f"Romance weight was {profile['Romantic Movies']} (expected < 0.0)"
    print(f"[PASSED] Behavioral Preference Profile Weight Updates: Sci-Fi ({profile['Sci-Fi & Fantasy']}), Romance ({profile['Romantic Movies']})")

    # 2. Offline IR Metric Benchmarks
    recommended = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    ground_truth = {1, 3, 5, 7, 11}

    rec10 = RecommendationEvaluator.recall_at_k(recommended, ground_truth, k=10)
    prec10 = RecommendationEvaluator.precision_at_k(recommended, ground_truth, k=10)
    ndcg10 = RecommendationEvaluator.ndcg_at_k(recommended, ground_truth, k=10)
    mrr = RecommendationEvaluator.mrr_at_k(recommended, ground_truth, k=10)
    hit_rate = RecommendationEvaluator.hit_rate_at_k(recommended, ground_truth, k=10)

    assert rec10 == 0.80, f"Recall@10 was {rec10:.2f} (expected 0.80)"
    assert prec10 == 0.40, f"Precision@10 was {prec10:.2f} (expected 0.40)"
    assert ndcg10 > 0.70, f"NDCG@10 was {ndcg10:.2f} (expected > 0.70)"
    assert mrr == 1.0, f"MRR was {mrr:.2f} (expected 1.0)"

    print(f"[PASSED] Recall@10: {rec10:.2f}")
    print(f"[PASSED] Precision@10: {prec10:.2f}")
    print(f"[PASSED] NDCG@10: {ndcg10:.2f}")
    print(f"[PASSED] MRR: {mrr:.2f}")
    print(f"[PASSED] HitRate@10: {hit_rate:.1f}")

if __name__ == "__main__":
    run_gate_4_recommendation_quality_evaluation()
    print("\nALL GATE 4 RECOMMENDATION QUALITY EVALUATION TESTS PASSED (100%)!")
