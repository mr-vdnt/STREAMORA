import pytest
from services.content_intelligence.adapter import ContentIntelligenceAdapter
from services.content_intelligence.models import EdgeType
from services.retrieval.generators.knowledge_graph import KnowledgeGraphGenerator

@pytest.fixture
def mock_movies():
    return {
        1: {
            "title": "Inception",
            "director": "Christopher Nolan",
            "cast": "Leonardo DiCaprio, Joseph Gordon-Levitt",
            "genres": "Action|Sci-Fi",
            "themes": "Dreams, Reality, Time"
        },
        2: {
            "title": "Interstellar",
            "director": "Christopher Nolan",
            "cast": "Matthew McConaughey, Anne Hathaway",
            "genres": "Adventure|Sci-Fi",
            "themes": "Space, Time, Family"
        },
        3: {
            "title": "The Matrix",
            "director": "Lana Wachowski, Lilly Wachowski",
            "cast": "Keanu Reeves, Laurence Fishburne",
            "genres": "Action|Sci-Fi",
            "themes": "Dreams, Reality, AI"
        }
    }

@pytest.fixture
def adapter(mock_movies):
    return ContentIntelligenceAdapter(mock_movies)

def test_graph_initialization(adapter):
    stats = adapter.get_graph_statistics()
    assert stats["nodes_count"] > 10
    assert stats["edges_count"] > 10

def test_relationship_features(adapter):
    features = adapter.get_relationship_features(1, 2)
    # Both are Nolan movies
    assert features["shared_director_score"] > 0
    # Both explore Time
    assert features["shared_theme_score"] > 0
    assert features["graph_similarity"] > 0

    features_unrelated = adapter.get_relationship_features(2, 3)
    assert features_unrelated["shared_director_score"] == 0

def test_similar_candidates(adapter):
    # Inception and Interstellar are similar (Nolan, Sci-Fi, Time)
    candidates = adapter.get_similar_candidates([1], limit=5)
    c_ids = [c["content_id"] for c in candidates]
    assert 2 in c_ids # Interstellar should be related

def test_explanation_context(adapter):
    expl = adapter.get_explanation_context(1, 2)
    assert "Christopher Nolan" in expl
    assert "Time" in expl

def test_knowledge_graph_generator(mock_movies, adapter):
    gen = KnowledgeGraphGenerator(mock_movies, adapter)
    context = {"seed_ids": [1]}
    cands = gen.retrieve(context)
    assert len(cands) > 0
    c_ids = [c["content_id"] for c in cands]
    assert 2 in c_ids
