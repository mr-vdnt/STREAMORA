"""
DAP Quality Scorer Stage — Metadata completeness scoring and quality filtering.
"""
from __future__ import annotations
import logging
from typing import Dict
from core.config import settings
from services.ingestion.contracts import PipelineStage, PipelineMessage, MessageType
from services.ingestion.dtos import NormalizedContentDTO, QualityReport

logger = logging.getLogger("streamora.ingestion.quality_scorer")


class QualityScorerStage(PipelineStage):
    """Scores metadata completeness (0-100) and filters low-quality entities.
    
    Consumes: CONFLICT_RESOLVED messages
    Emits: QUALITY_SCORED messages (or FAILED if quality is below threshold)
    
    Scoring weights:
    - Title: 20 points (required)
    - Overview: 20 points
    - Poster URL: 15 points
    - Backdrop URL: 10 points
    - Cast/Crew: 15 points (at least 3 items)
    - Genres: 10 points (at least 1)
    - Release Date / Runtime: 10 points
    """

    def __init__(self, quality_threshold: float = None):
        self.quality_threshold = (
            quality_threshold
            if quality_threshold is not None
            else getattr(settings.ingestion, "quality_threshold", 40.0)
        )

    @property
    def stage_name(self) -> str:
        return "quality_scorer"

    async def process(self, message: PipelineMessage) -> PipelineMessage:
        normalized: NormalizedContentDTO = message.payload
        resolution = message.metadata.get("resolution")

        # If resolution action is "skip", bypass scoring
        if resolution and resolution.action == "skip":
            return PipelineMessage(
                message_type=MessageType.QUALITY_SCORED,
                job_id=message.job_id,
                connector_name=message.connector_name,
                external_id=message.external_id,
                entity_type=message.entity_type,
                payload=normalized,
                raw_payload_id=message.raw_payload_id,
                metadata={
                    **message.metadata,
                    "quality_report": QualityReport(score=0.0, meets_threshold=True),
                },
                trace_id=message.trace_id,
            )

        report = self.score(normalized)

        if not report.meets_threshold:
            logger.warning(
                f"Quality score {report.score:.1f} below threshold {self.quality_threshold} "
                f"for {message.external_id} ({normalized.title})"
            )
            return PipelineMessage(
                message_type=MessageType.FAILED,
                job_id=message.job_id,
                connector_name=message.connector_name,
                external_id=message.external_id,
                entity_type=message.entity_type,
                payload=message.payload,
                raw_payload_id=message.raw_payload_id,
                error=f"quality_scorer: Score {report.score:.1f} below threshold {self.quality_threshold}",
                metadata={
                    **message.metadata,
                    "quality_report": report,
                    "failure_stage": "quality_scorer",
                },
                trace_id=message.trace_id,
            )

        return PipelineMessage(
            message_type=MessageType.QUALITY_SCORED,
            job_id=message.job_id,
            connector_name=message.connector_name,
            external_id=message.external_id,
            entity_type=message.entity_type,
            payload=normalized,
            raw_payload_id=message.raw_payload_id,
            metadata={**message.metadata, "quality_report": report},
            trace_id=message.trace_id,
        )

    def score(self, normalized: NormalizedContentDTO) -> QualityReport:
        """Calculate quality score (0.0 - 100.0) based on completeness."""
        score = 0.0
        penalties: Dict[str, float] = {}

        # Title (20 pts)
        if normalized.title and normalized.title.strip():
            score += 20.0
        else:
            penalties["missing_title"] = 20.0

        # Overview (20 pts)
        if normalized.overview and len(normalized.overview.strip()) >= 20:
            score += 20.0
        elif normalized.overview and len(normalized.overview.strip()) > 0:
            score += 10.0
            penalties["short_overview"] = 10.0
        else:
            penalties["missing_overview"] = 20.0

        # Poster URL (15 pts)
        if normalized.poster_url and normalized.poster_url.strip():
            score += 15.0
        else:
            penalties["missing_poster"] = 15.0

        # Backdrop URL (10 pts)
        if normalized.backdrop_url and normalized.backdrop_url.strip():
            score += 10.0
        else:
            penalties["missing_backdrop"] = 10.0

        # Cast & Crew (15 pts)
        total_people = len(normalized.cast) + len(normalized.crew)
        if total_people >= 5:
            score += 15.0
        elif total_people >= 1:
            score += 8.0
            penalties["sparse_cast_crew"] = 7.0
        else:
            penalties["missing_cast_crew"] = 15.0

        # Genres (10 pts)
        if len(normalized.genres) >= 2:
            score += 10.0
        elif len(normalized.genres) == 1:
            score += 5.0
            penalties["single_genre"] = 5.0
        else:
            penalties["missing_genres"] = 10.0

        # Release Date & Runtime (10 pts)
        date_score = 5.0 if normalized.release_date else 0.0
        runtime_score = 5.0 if (normalized.runtime and normalized.runtime > 0) else 0.0
        score += date_score + runtime_score
        if not normalized.release_date:
            penalties["missing_release_date"] = 5.0
        if not normalized.runtime or normalized.runtime <= 0:
            penalties["missing_runtime"] = 5.0

        meets_threshold = score >= self.quality_threshold
        return QualityReport(
            score=round(score, 1),
            penalties=penalties,
            meets_threshold=meets_threshold,
        )
