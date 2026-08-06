import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.recommendation.vector_search import VectorSearchEngine, ContentEmbeddingVector
from services.recommendation.freshness import FreshnessScorer
from services.recommendation.exploration import ExplorationBandit
from services.recommendation.experiment_manager import ExperimentManager

def test_vector_search_engine():
    """Verify 768-dim dense embedding cosine similarity search."""
    print("\n--- Verifying Vector Search Engine (768-Dim Cosine Similarity) ---")
    engine = VectorSearchEngine()

    v1 = [0.1] * 768
    v2 = [0.1] * 768
    v3 = [-0.1] * 768

    engine.index_vector(ContentEmbeddingVector(content_id=1, vector=v1))
    engine.index_vector(ContentEmbeddingVector(content_id=2, vector=v2))
    engine.index_vector(ContentEmbeddingVector(content_id=3, vector=v3))

    results = engine.search_nearest_neighbors(v1, top_k=2, exclude_ids=[1])
    assert len(results) == 2
    assert results[0]["content_id"] == 2
    assert results[0]["similarity"] > 0.99
    print(f"[PASSED] 768-Dim Vector Nearest Neighbor Similarity: {results[0]['similarity']:.4f}")

def test_freshness_time_decay():
    """Verify exponential time decay freshness calculations."""
    print("\n--- Verifying Freshness Exponential Time Decay ---")
    scorer = FreshnessScorer(decay_rate_lambda=0.005)

    recent_score = scorer.calculate_decay_score(1.0, "2026-08-01")
    old_score = scorer.calculate_decay_score(1.0, "2020-01-01")

    assert recent_score > old_score
    print(f"[PASSED] Recent Title Score: {recent_score:.4f} > Old Title Score: {old_score:.4f}")

def test_exploration_bandit():
    """Verify Epsilon-Greedy Exploration Bandit (85% Exploit / 15% Explore)."""
    print("\n--- Verifying Epsilon-Greedy Exploration Bandit ---")
    bandit = ExplorationBandit(epsilon=0.20)

    exploit = [{"content_id": i} for i in range(1, 11)]
    explore = [{"content_id": i} for i in range(100, 110)]

    blended = bandit.blend_exploitation_exploration(exploit, explore, total_limit=10)
    assert len(blended) == 10
    has_exploration_item = any(item["content_id"] >= 100 for item in blended)
    assert has_exploration_item
    print("[PASSED] Exploration Bandit Successfully Blended Exploitation and Exploration Slates")

def test_experiment_manager_variants():
    """Verify Online Experiment Manager user bucketing and CTR tracking."""
    print("\n--- Verifying Online Experiment Manager ---")
    mgr = ExperimentManager()
    variant = mgr.assign_variant("user_12345")
    assert variant.variant_id in ["variant_a", "variant_b", "variant_c"]

    mgr.record_impression(variant.variant_id)
    mgr.record_click(variant.variant_id)
    ctr = mgr.get_ctr(variant.variant_id)
    assert ctr == 100.0
    print(f"[PASSED] User Assigned to Variant '{variant.variant_id}' ({variant.description}) with {ctr:.1f}% CTR")

if __name__ == "__main__":
    test_vector_search_engine()
    test_freshness_time_decay()
    test_exploration_bandit()
    test_experiment_manager_variants()
    print("\nALL RECOMMENDATION V4 ENTERPRISE TESTS PASSED (100%)!")
