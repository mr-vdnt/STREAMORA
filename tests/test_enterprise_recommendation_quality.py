import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.knowledge.taxonomy import FactCategory, Predicate
from services.recommendation.graph_relationship import KIPRecommendationGraph, RelationshipEdge
from services.recommendation.recommendation_pipeline import RecommendationPipeline

def test_universe_vs_studio_taxonomy_separation():
    """Verify Universe vs Studio taxonomy concept separation."""
    print("\n--- Verifying Universe vs Studio Taxonomy Separation ---")
    assert FactCategory.UNIVERSE.value == "universe"
    assert FactCategory.STUDIO.value == "studio"
    assert Predicate.BELONGS_TO_UNIVERSE == "belongs_to_universe"
    assert Predicate.PRODUCED_BY_STUDIO == "produced_by_studio"
    print("[PASSED] Universe vs Studio Taxonomy Concepts Formally Modeled")

def test_kip_relationship_graph_and_22_signal_scoring():
    """Verify KIP Relationship Graph weighted edges and 22-signal scoring engine."""
    print("\n--- Verifying KIP Relationship Graph & 22-Signal Scoring ---")
    graph = KIPRecommendationGraph()
    edge = RelationshipEdge(
        source_content_id=1,
        target_content_id=2,
        relationship_type="universe",
        strength_weight=0.93,
        rationale="Shared MCU Multiverse Timeline"
    )
    graph.add_edge(edge)

    edges = graph.get_related_edges(1, "universe")
    assert len(edges) == 1
    assert edges[0].strength_weight == 0.93

    # Test 22-Signal Scoring Engine
    m1 = {"franchise": "Spider-Man", "universe": "MCU", "studio": "Marvel", "cast": ["Tom Holland"], "genres": ["Action"]}
    m2 = {"franchise": "Spider-Man", "universe": "MCU", "studio": "Sony", "cast": ["Tom Holland"], "genres": ["Action"]}
    score = graph.calculate_22_signal_similarity(m1, m2)
    assert score >= 0.70, f"Scoring engine returned {score:.2f} (expected >= 0.70)"
    print(f"[PASSED] 22-Signal Scoring Similarity Engine Score: {score:.2f}")

def test_multi_shelf_generation_and_cross_shelf_deduplication():
    """Verify contextual shelf generation, cross-shelf deduplication, and rich explanations."""
    print("\n--- Verifying Multi-Shelf Contextual Slate Generation & Deduplication ---")
    pipeline = RecommendationPipeline()
    shelves = pipeline.generate_contextual_shelves(content_id=1, user_id="demo_user")

    assert len(shelves) >= 3, f"Shelves count was {len(shelves)} (expected >= 3)"

    seen_ids = set()
    for shelf in shelves:
        assert "title" in shelf
        assert "rationale" in shelf
        assert len(shelf["rationale"]) >= 2
        for item in shelf["items"]:
            # Verify cross-shelf deduplication
            assert item["id"] not in seen_ids, f"Duplicate content_id {item['id']} found in shelf {shelf['title']}"
            seen_ids.add(item["id"])

    print(f"[PASSED] Multi-Shelf Slate Returned {len(shelves)} Unique Shelves with Cross-Shelf Deduplication")
    print(f"[PASSED] Rich Explanations Validated: {shelves[0]['rationale'][0].encode('ascii', 'ignore').decode('ascii')}")

if __name__ == "__main__":
    test_universe_vs_studio_taxonomy_separation()
    test_kip_relationship_graph_and_22_signal_scoring()
    test_multi_shelf_generation_and_cross_shelf_deduplication()
    print("\nALL ENTERPRISE RECOMMENDATION QUALITY TESTS PASSED (100%)!")
