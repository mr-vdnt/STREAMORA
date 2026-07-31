import pytest
from services.repository.catalog_db import (
    CatalogRepository, Content, ContentMetadata, ContentArtwork, ContentStatistics, MovieDetails,
    ExternalIdentifier, ContentRelationship, OutboxEvent, SearchDocument, RecommendationFeatures
)
from services.catalog.slug_service import SlugService
from services.catalog.events.publisher import OutboxEventPublisher
from services.catalog.search_prep_service import SearchPreparationService
from services.catalog.recommendation_prep_service import RecommendationPreparationService

def test_canonical_catalog_aggregate_and_relationships():
    repo = CatalogRepository()
    session = repo.get_session()

    # Create Content Aggregate Root
    content = Content(
        slug=SlugService.generate_unique_slug(session, "Inception Canonical", "2010"),
        entity_type="movie"
    )
    session.add(content)
    session.flush()

    meta = ContentMetadata(content_id=content.id, title="Inception Canonical", release_date="2010-07-16", runtime=148)
    art = ContentArtwork(content_id=content.id, poster_url="/poster.jpg", backdrop_url="/backdrop.jpg")
    stats = ContentStatistics(content_id=content.id, popularity=95.0, average_rating=8.8)
    details = MovieDetails(content_id=content.id, budget="$160,000,000", revenue="$830,000,000")
    
    session.add_all([meta, art, stats, details])

    import uuid
    rand_suffix = uuid.uuid4().hex[:8]
    ext_tmdb = ExternalIdentifier(content_id=content.id, provider_name="tmdb", external_id=f"27205_{rand_suffix}")
    ext_imdb = ExternalIdentifier(content_id=content.id, provider_name="imdb", external_id=f"tt1375666_{rand_suffix}")
    session.add_all([ext_tmdb, ext_imdb])

    # Outbox Event Publishing
    OutboxEventPublisher.publish(session, "Content", content.uuid, "ContentCreated", {"title": "Inception Canonical"})

    session.commit()

    # Assertions
    fetched = session.query(Content).filter(Content.id == content.id).first()
    assert fetched is not None
    assert fetched.metadata_rel.title == "Inception Canonical"
    assert fetched.statistics_rel.average_rating == 8.8
    assert len(fetched.external_ids) == 2

    # Graph Projection Test
    node = fetched.to_graph_node()
    assert node["node_uuid"] == fetched.uuid
    assert node["node_type"] == "movie"

    # Search & Recommendation Prep
    SearchPreparationService().prepare_search_document(session, content.id)
    RecommendationPreparationService().prepare_features(session, content.id)

    search_doc = session.query(SearchDocument).filter(SearchDocument.content_id == content.id).first()
    assert search_doc is not None
    assert search_doc.ascii_title == "inception canonical"

    rec_feat = session.query(RecommendationFeatures).filter(RecommendationFeatures.content_id == content.id).first()
    assert rec_feat is not None
    assert rec_feat.embedding_provider == "sentence-transformers"

    session.close()
