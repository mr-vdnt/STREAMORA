from __future__ import annotations
import asyncio
import pytest
from services.repository.catalog_db import CatalogRepository, KnowledgeFact, KnowledgeSnapshot, IntelligenceProfile
from services.knowledge.pipeline import KnowledgePipeline
from services.knowledge.extractor import KnowledgeExtractor
from services.knowledge.materializer import ProfileMaterializer
from services.knowledge.dtos import KnowledgeFactDTO

@pytest.fixture
def catalog_repo():
    return CatalogRepository()

@pytest.fixture
def knowledge_pipeline(catalog_repo):
    return KnowledgePipeline(repo=catalog_repo)

def test_knowledge_extractor_baseline():
    extractor = KnowledgeExtractor()
    sample_data = {
        "title": "Inception",
        "overview": "A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.",
        "genres": ["Action", "Science Fiction", "Adventure"],
        "release_date": "2010-07-16",
        "cast": [{"name": "Leonardo DiCaprio", "character_name": "Cobb"}]
    }

    facts = extractor.extract_baseline_facts(content_id=1, content_data=sample_data)
    assert len(facts) > 0

    categories = {f.category for f in facts}
    assert "theme" in categories
    assert "topic" in categories
    assert "setting" in categories
    assert "character" in categories

    topic_values = [f.value for f in facts if f.category == "topic"]
    assert "dream-manipulation" in topic_values

def test_snapshot_hash_generation():
    materializer = ProfileMaterializer()
    facts = [
        KnowledgeFactDTO(content_id=1, category="theme", predicate="has_theme", value="genre-action", confidence=0.95),
        KnowledgeFactDTO(content_id=1, category="mood", predicate="has_mood", value="suspenseful", confidence=0.88)
    ]
    h1 = materializer.generate_snapshot_hash(facts)
    h2 = materializer.generate_snapshot_hash(facts)
    assert h1 == h2
    assert len(h1) == 64

def test_knowledge_pipeline_e2e(knowledge_pipeline, catalog_repo):
    # Process content item 1 (Inception Canonical)
    profile_dto = asyncio.run(knowledge_pipeline.process_content(content_id=1))

    assert profile_dto is not None
    assert profile_dto.content_id == 1
    assert profile_dto.fact_count > 0
    assert profile_dto.summary_short is not None
    assert profile_dto.summary_medium is not None
    assert profile_dto.summary_deep is not None

    # Verify DB persistence
    with catalog_repo.get_session() as session:
        db_facts = session.query(KnowledgeFact).filter(KnowledgeFact.content_id == 1).all()
        assert len(db_facts) >= profile_dto.fact_count

        db_snapshot = session.query(KnowledgeSnapshot).filter(KnowledgeSnapshot.content_id == 1).first()
        assert db_snapshot is not None
        assert len(db_snapshot.knowledge_hash) == 64

        db_profile = session.query(IntelligenceProfile).filter(IntelligenceProfile.content_id == 1).first()
        assert db_profile is not None
        assert db_profile.summary_short == profile_dto.summary_short
