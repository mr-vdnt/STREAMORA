from __future__ import annotations
import asyncio
import pytest
from services.repository.catalog_db import CatalogRepository, UserInteractionEvent
from services.recommendation.user_intelligence.user_intelligence import UserIntelligencePlatform
from services.recommendation.planner.planner import RecommendationPlanner
from services.recommendation.planner.optimizer import RecommendationOptimizer
from services.recommendation.fusion.candidate_fusion import RecommendationCandidateFuser
from services.recommendation.diversification.diversifier import RecommendationDiversifier
from services.recommendation.recommendation_pipeline import RecommendationPipeline
from services.recommendation.orchestrator.home_feed_orchestrator import HomeFeedOrchestrator
from services.recommendation.analytics.telemetry import FeedbackTelemetryLogger

@pytest.fixture
def catalog_repo():
    return CatalogRepository()

def test_user_intelligence_platform():
    platform = UserIntelligencePlatform()
    profile = platform.get_profile("test_user")

    assert profile.user_id == "test_user"
    assert "Sci-Fi" in profile.genre_affinities
    assert "dream" in profile.theme_affinities

def test_recommendation_planner_and_optimizer():
    planner = RecommendationPlanner()
    optimizer = RecommendationOptimizer()

    plan = planner.create_plan(user_id="test_user", slate_type="personalized_home")
    assert plan.slate_type == "personalized_home"
    assert "collaborative" in plan.active_generators

    opt_plan = optimizer.optimize_plan(plan)
    assert opt_plan is not None

def test_candidate_fusion_provenance():
    fuser = RecommendationCandidateFuser()
    from services.recommendation.dtos import RecommendationCandidateDTO

    c1 = RecommendationCandidateDTO(content_id=1, generator_name="collaborative", score=0.9, reason="User co-occurrence")
    c2 = RecommendationCandidateDTO(content_id=1, generator_name="content_based", score=0.8, reason="Theme match")

    fused = fuser.fuse_candidates([c1, c2])
    assert len(fused) == 1
    assert fused[0].content_id == 1
    assert "collaborative" in fused[0].provenance_metadata["sources"]
    assert "content_based" in fused[0].provenance_metadata["sources"]

def test_recommendation_pipeline_e2e(catalog_repo):
    pipeline = RecommendationPipeline(repo=catalog_repo)
    shelf = asyncio.run(pipeline.generate_slate(user_id="test_user", slate_type="personalized_home", limit=10))

    assert shelf is not None
    assert shelf.slate_type == "personalized_home"
    assert len(shelf.items) > 0

    first_item = shelf.items[0]
    assert first_item.content_id > 0
    assert first_item.explanation is not None

def test_home_feed_orchestrator(catalog_repo):
    orchestrator = HomeFeedOrchestrator(repo=catalog_repo)
    feed = asyncio.run(orchestrator.build_home_feed(user_id="test_user"))

    assert feed is not None
    assert feed.user_id == "test_user"
    assert len(feed.shelves) > 0
    assert feed.latency_ms > 0.0

def test_feedback_telemetry(catalog_repo):
    telemetry = FeedbackTelemetryLogger(repo=catalog_repo)
    event_id = telemetry.log_interaction(user_id="test_user", content_id=1, event_type="watch", weight=1.0)

    assert event_id > 0
    with catalog_repo.get_session() as session:
        evt = session.query(UserInteractionEvent).filter(UserInteractionEvent.id == event_id).first()
        assert evt is not None
        assert evt.user_id == "test_user"
