import pytest
from services.ranking.decision_engine import DecisionEngine
from services.ranking.models import RecommendationPackage

@pytest.fixture
def sample_movies_db():
    return {
        1: {"item_id": 1, "title": "Batman Begins", "director": "Christopher Nolan", "franchise": "Batman", "genres": "Action|Crime|Drama", "cast": "Christian Bale, Michael Caine"},
        2: {"item_id": 2, "title": "The Dark Knight", "director": "Christopher Nolan", "franchise": "Batman", "genres": "Action|Crime|Drama|Thriller", "cast": "Christian Bale, Heath Ledger"},
        3: {"item_id": 3, "title": "The Dark Knight Rises", "director": "Christopher Nolan", "franchise": "Batman", "genres": "Action|Thriller", "cast": "Christian Bale, Tom Hardy"},
        4: {"item_id": 4, "title": "Inception", "director": "Christopher Nolan", "franchise": None, "genres": "Action|Sci-Fi|Thriller", "cast": "Leonardo DiCaprio, Joseph Gordon-Levitt"},
        5: {"item_id": 5, "title": "Prisoners", "director": "Denis Villeneuve", "franchise": None, "genres": "Crime|Drama|Mystery", "cast": "Hugh Jackman, Jake Gyllenhaal"},
    }

@pytest.fixture
def sample_candidate_pool():
    return {
        "query_contract": {
            "reference_title": "Batman Begins",
            "entities": {
                "directors": ["Christopher Nolan"],
                "genres": ["Action", "Thriller"]
            }
        },
        "candidates": [
            {"content_id": 1, "retrieval": {"fusion_score": 1.0, "generators": [{"name": "exact"}]}}, # Reference movie
            {"content_id": 2, "retrieval": {"fusion_score": 0.9, "generators": [{"name": "exact"}, {"name": "semantic"}]}},
            {"content_id": 3, "retrieval": {"fusion_score": 0.8, "generators": [{"name": "exact"}]}},
            {"content_id": 4, "retrieval": {"fusion_score": 0.6, "generators": [{"name": "semantic"}]}},
            {"content_id": 5, "retrieval": {"fusion_score": 0.1, "generators": [{"name": "metadata"}]}},
            {"content_id": 999, "retrieval": {"fusion_score": 1.0, "generators": [{"name": "exact"}]}}, # Doesn't exist in DB
        ]
    }

def test_decision_engine_flow(sample_movies_db, sample_candidate_pool):
    engine = DecisionEngine(sample_movies_db)
    
    # Process
    package = engine.process(sample_candidate_pool)
    
    assert isinstance(package, RecommendationPackage)
    
    # Validate diagnostics
    diag = package.diagnostics
    assert diag.candidates_in == 6
    # 1 removed for being reference title (ID 1)
    # 1 removed for missing from DB (ID 999)
    # So valid candidates = 4 (IDs 2, 3, 4, 5)
    
    # The diversity limit for franchise is 2. 
    # But reference movie (Batman Begins) doesn't count towards output diversity because it's stripped early.
    # IDs 2 and 3 are in the "Batman" franchise. That's 2. So both are kept.
    # ID 4 is Nolan, but franchise is None.
    # ID 5 is Villeneuve.
    # Let's adjust the test to force a diversity rejection. 
    # Actually wait, director limit is 2.
    # IDs 2, 3, 4 are all Nolan (director).
    # Since director limit is 2, the 3rd Nolan movie should be dropped!
    # Valid candidates: [2, 3, 4, 5]. 
    # 2, 3, 4 are Nolan.
    # Sorted by score (roughly): 2 (fusion 0.9, matches Nolan), 3 (fusion 0.8, matches Nolan), 4 (fusion 0.6, matches Nolan).
    # Diversity will drop 4. So diversity_replacements should be 1.
    assert diag.diversity_replacements == 1
    
    assert len(package.recommendations) == 3
    
    # Check that ID 1 (reference) is not in recommendations
    ids = [r.content_id for r in package.recommendations]
    assert 1 not in ids
    assert 999 not in ids
    assert 2 in ids
    assert 3 in ids
    assert 5 in ids
    assert 4 not in ids # Dropped by director diversity limit
    
    # Check Explainability & Confidence
    top_rec = package.recommendations[0]
    assert top_rec.ranking.rank == 1
    assert "DIRECTOR_MATCH" in top_rec.explainability.reason_codes
    assert "GENRE_MATCH" in top_rec.explainability.reason_codes
    assert top_rec.ranking.confidence >= 0.5 # Has 2 generators, so baseline 0.5 + 0.15 + 0.1 = 0.75
