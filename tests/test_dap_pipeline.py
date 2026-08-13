"""
Phase 3 — Data Acquisition Platform (DAP) Test Suite.

Verifies:
- Validator stage
- Normalizer stage
- Entity Resolver stage
- Conflict Resolver stage
- Quality Scorer stage
- CatalogWriter command execution
- End-to-end Pipeline integration
"""
import pytest
import asyncio
import uuid
from services.repository.catalog_db import (
    CatalogRepository, Content, ContentMetadata, ContentArtwork, ContentStatistics,
    ExternalIdentifier, OutboxEvent, IngestionJob, RawPayload, IngestionProvenance
)
from services.ingestion.contracts import PipelineMessage, MessageType
from services.ingestion.dtos import RawPayloadDTO, NormalizedContentDTO, PersonDTO
from services.ingestion.commands import CreateContentCommand, UpdateContentCommand
from services.ingestion.stages.validator import ValidatorStage
from services.ingestion.stages.normalizer import NormalizerStage
from services.ingestion.stages.resolver import EntityResolverStage
from services.ingestion.stages.conflict_resolver import ConflictResolverStage
from services.ingestion.stages.quality_scorer import QualityScorerStage
from services.ingestion.catalog_writer import CatalogWriter
from services.ingestion.pipeline import DataAcquisitionPipeline


@pytest.fixture
def anyio_backend():
    return 'asyncio'


@pytest.fixture
def repo():
    """Create fresh isolated catalog repository for testing."""
    r = CatalogRepository()
    return r


@pytest.fixture
def sample_tmdb_movie():
    return {
        "id": 99927205,
        "title": "Inception DAP Test",
        "original_title": "Inception DAP Test",
        "overview": "A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.",
        "release_date": "2010-07-16",
        "runtime": 148,
        "original_language": "en",
        "vote_average": 8.4,
        "vote_count": 34000,
        "popularity": 125.5,
        "poster_path": "/oYuLEW922zkoBvoO3hRBG me9b6.jpg",
        "backdrop_path": "/s3TBrRGB1iav7ySaDxmTe21w22n.jpg",
        "genres": [{"id": 28, "name": "Action"}, {"id": 878, "name": "Science Fiction"}],
        "credits": {
            "cast": [
                {"name": "Leonardo DiCaprio", "character": "Cobb", "order": 0},
                {"name": "Joseph Gordon-Levitt", "character": "Arthur", "order": 1},
            ],
            "crew": [
                {"name": "Christopher Nolan", "job": "Director"},
            ],
        },
    }


# --- 1. Validator Tests ---

@pytest.mark.anyio
async def test_validator_valid_payload(sample_tmdb_movie):
    validator = ValidatorStage()
    msg = PipelineMessage(
        message_type=MessageType.RAW_PAYLOAD,
        job_id=1,
        connector_name="tmdb",
        external_id="27205",
        entity_type="movie",
        payload=sample_tmdb_movie,
    )
    result = await validator.process(msg)
    assert result.message_type == MessageType.VALIDATED


@pytest.mark.anyio
async def test_validator_missing_title():
    validator = ValidatorStage()
    msg = PipelineMessage(
        message_type=MessageType.RAW_PAYLOAD,
        job_id=1,
        connector_name="tmdb",
        external_id="123",
        entity_type="movie",
        payload={"id": 123},  # missing title
    )
    result = await validator.process(msg)
    assert result.message_type == MessageType.FAILED
    assert "validation" in result.error


# --- 2. Normalizer Tests ---

@pytest.mark.anyio
async def test_normalizer_tmdb(sample_tmdb_movie):
    normalizer = NormalizerStage()
    msg = PipelineMessage(
        message_type=MessageType.VALIDATED,
        job_id=1,
        connector_name="tmdb",
        external_id="99927205",
        entity_type="movie",
        payload=sample_tmdb_movie,
        metadata={"payload_hash": "hash123"},
    )
    result = await normalizer.process(msg)
    assert result.message_type == MessageType.NORMALIZED
    norm: NormalizedContentDTO = result.payload

    assert norm.title == "Inception DAP Test"
    assert norm.external_ids["tmdb"] == "99927205"
    assert norm.runtime == 148
    assert norm.genres == ["Action", "Science Fiction"]
    assert norm.poster_url.startswith("https://image.tmdb.org/")
    assert len(norm.cast) == 2
    assert norm.cast[0].name == "Leonardo DiCaprio"
    assert len(norm.crew) == 1
    assert norm.crew[0].name == "Christopher Nolan"


# --- 3. Entity Resolver Tests ---

@pytest.mark.anyio
async def test_resolver_create(repo):
    resolver = EntityResolverStage(repo)
    norm = NormalizedContentDTO(
        external_ids={"tmdb": "99999"},
        entity_type="movie",
        title="Unique Film 2026",
    )
    msg = PipelineMessage(
        message_type=MessageType.NORMALIZED,
        job_id=1,
        connector_name="tmdb",
        external_id="99999",
        entity_type="movie",
        payload=norm,
    )
    result = await resolver.process(msg)
    assert result.message_type == MessageType.RESOLVED
    resolution = result.metadata["resolution"]
    assert resolution.action == "create"
    assert resolution.confidence == 0.0


# --- 4. Quality Scorer Tests ---

def test_quality_scorer_complete():
    scorer = QualityScorerStage(quality_threshold=40.0)
    norm = NormalizedContentDTO(
        external_ids={"tmdb": "1"},
        entity_type="movie",
        title="High Quality Movie",
        overview="This is a long overview of the movie that exceeds twenty characters.",
        poster_url="http://example.com/poster.jpg",
        backdrop_url="http://example.com/backdrop.jpg",
        release_date="2026-01-01",
        runtime=120,
        genres=["Action", "Sci-Fi"],
        cast=[PersonDTO(name="Actor 1", role="actor")],
    )
    report = scorer.score(norm)
    assert report.score >= 80.0
    assert report.meets_threshold is True


def test_quality_scorer_incomplete():
    scorer = QualityScorerStage(quality_threshold=40.0)
    norm = NormalizedContentDTO(
        external_ids={"tmdb": "2"},
        entity_type="movie",
        title="Bare Minimum",
    )
    report = scorer.score(norm)
    assert report.score < 40.0
    assert report.meets_threshold is False


# --- 5. CatalogWriter Command Execution Tests ---

def test_catalog_writer_create_command(repo):
    writer = CatalogWriter(repo)
    norm = NormalizedContentDTO(
        external_ids={"tmdb": "cmd_test_27205"},
        entity_type="movie",
        title="Inception Command Test",
        overview="Dream heist",
        release_date="2010-07-16",
        runtime=148,
        genres=["Sci-Fi"],
        poster_url="http://example.com/inception.jpg",
        popularity=120.0,
        average_rating=8.4,
    )
    cmd = CreateContentCommand(normalized=norm, source_connector="tmdb")

    result = writer.execute_create(cmd, quality_score=90.0)
    assert result.success is True
    assert result.action == "created"
    assert result.content_id is not None

    # Verify DB records
    with repo.get_session() as session:
        content = session.query(Content).filter(Content.id == result.content_id).first()
        assert content is not None
        assert content.slug.startswith("inception")

        meta = session.query(ContentMetadata).filter(ContentMetadata.content_id == result.content_id).first()
        assert meta.title == "Inception Command Test"
        assert meta.runtime == 148

        ext = session.query(ExternalIdentifier).filter(
            ExternalIdentifier.content_id == result.content_id,
            ExternalIdentifier.provider_name == "tmdb"
        ).first()
        assert ext.external_id == "cmd_test_27205"

        prov = session.query(IngestionProvenance).filter(
            IngestionProvenance.content_id == result.content_id
        ).first()
        assert prov.quality_score == 90.0

        # Verify OutboxEvent
        outbox = session.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(result.content_id)
        ).first()
        assert outbox is not None
        assert outbox.event_type == "content.created"


# --- 6. End-to-End Pipeline Integration Test ---

@pytest.mark.anyio
async def test_e2e_dap_pipeline(repo, sample_tmdb_movie):
    unique_ext_id = f"e2e_test_{uuid.uuid4().hex[:8]}"
    movie_data = dict(sample_tmdb_movie)
    movie_data["id"] = unique_ext_id
    movie_data["title"] = f"E2E Unique Title {unique_ext_id}"

    pipeline = DataAcquisitionPipeline(repo)
    raw_dto = RawPayloadDTO(
        connector_name="tmdb",
        external_id=unique_ext_id,
        entity_type="movie",
        raw_data=movie_data,
    )

    result = await pipeline.process_raw_payload(raw_dto, job_id=1)

    assert result.success is True
    assert result.action == "created"
    assert result.content_id is not None

    # Re-run same payload -> ConflictResolver & EntityResolver should detect duplicate and skip/update
    result_dup = await pipeline.process_raw_payload(raw_dto, job_id=1)
    assert result_dup.success is True
    assert result_dup.action in ("skipped", "updated")


# --- 7. IMDb Canonical Precedence & Security Tests ---

@pytest.mark.anyio
async def test_imdb_connector_circuit_breaker():
    from services.ingestion.connectors.imdb_connector import IMDbConnector
    connector = IMDbConnector()

    assert connector.get_manifest().name == "imdb"
    assert connector.circuit_breaker.state == "CLOSED"

    # Test fallback payload when disabled/unconfigured
    payload = await connector.fetch_by_id("tt1375666", "movie")
    assert payload is not None
    assert payload.connector_name == "imdb"
    assert payload.external_id == "tt1375666"

    await connector.close()


@pytest.mark.anyio
async def test_normalizer_imdb_runtime_seconds():
    normalizer = NormalizerStage()
    imdb_raw = {
        "id": "tt1375666",
        "canonicalId": "tt1375666",
        "titleText": {"text": "Inception IMDb Authority"},
        "runtime": {"seconds": 8880},  # 148 minutes
        "ratingsSummary": {"aggregateRating": 8.8, "voteCount": 2400000},
        "genres": {"genres": [{"text": "Action"}, {"text": "Sci-Fi"}]},
    }
    msg = PipelineMessage(
        message_type=MessageType.VALIDATED,
        job_id=1,
        connector_name="imdb",
        external_id="tt1375666",
        entity_type="movie",
        payload=imdb_raw,
    )
    res = await normalizer.process(msg)
    assert res.message_type == MessageType.NORMALIZED
    norm: NormalizedContentDTO = res.payload

    assert norm.title == "Inception IMDb Authority"
    assert norm.runtime_seconds == 8880
    assert norm.runtime == 148
    assert norm.imdb_rating == 8.8
    assert norm.provenance["title"] == "imdb"
    assert norm.provenance["runtime_seconds"] == "imdb"


@pytest.mark.anyio
async def test_validator_reject_synthetic_placeholders():
    validator = ValidatorStage()

    # Reject synthetic title
    msg_fake_title = PipelineMessage(
        message_type=MessageType.RAW_PAYLOAD,
        job_id=1,
        connector_name="tmdb",
        external_id="123",
        entity_type="movie",
        payload={"id": 123, "title": "Unknown Director"},
    )
    res = await validator.process(msg_fake_title)
    assert res.message_type == MessageType.FAILED
    assert "synthetic placeholder" in res.error
