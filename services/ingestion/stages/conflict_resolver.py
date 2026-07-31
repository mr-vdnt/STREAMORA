"""
DAP Conflict Resolver Stage — Field-level merge strategy for content updates.
"""
from __future__ import annotations
import logging
from typing import Dict, Tuple, Any
from services.ingestion.contracts import PipelineStage, PipelineMessage, MessageType
from services.ingestion.dtos import NormalizedContentDTO, ResolutionResult
from services.repository.catalog_db import CatalogRepository, Content, ContentMetadata, ContentArtwork, ContentStatistics

logger = logging.getLogger("streamora.ingestion.conflict_resolver")


class ConflictResolverStage(PipelineStage):
    """Determines field-level merge operations for content updates.
    
    Consumes: RESOLVED messages (with resolution action = "update")
    Emits: CONFLICT_RESOLVED messages (payload enriched with changed_fields)
    
    Merge strategies:
    - Freshness wins: More recent data overwrites stale data
    - Completeness wins: Non-empty field takes priority over empty
    - Never downgrade: A valid rating is never replaced by 0.0
    """

    def __init__(self, catalog_repo: CatalogRepository = None):
        self._repo = catalog_repo or CatalogRepository()

    @property
    def stage_name(self) -> str:
        return "conflict_resolver"

    async def process(self, message: PipelineMessage) -> PipelineMessage:
        resolution: ResolutionResult = message.metadata.get("resolution")
        normalized: NormalizedContentDTO = message.payload

        # If action is "create", pass through — no conflict to resolve
        if not resolution or resolution.action == "create":
            return PipelineMessage(
                message_type=MessageType.CONFLICT_RESOLVED,
                job_id=message.job_id,
                connector_name=message.connector_name,
                external_id=message.external_id,
                entity_type=message.entity_type,
                payload=normalized,
                raw_payload_id=message.raw_payload_id,
                metadata={**message.metadata, "changed_fields": {}},
                trace_id=message.trace_id,
            )

        # For updates, compute field-level diff
        try:
            content_id = resolution.existing_content_id
            changed_fields = self._compute_diff(content_id, normalized)

            if not changed_fields:
                # No changes detected — mark as skip
                return PipelineMessage(
                    message_type=MessageType.CONFLICT_RESOLVED,
                    job_id=message.job_id,
                    connector_name=message.connector_name,
                    external_id=message.external_id,
                    entity_type=message.entity_type,
                    payload=normalized,
                    raw_payload_id=message.raw_payload_id,
                    metadata={
                        **message.metadata,
                        "changed_fields": {},
                        "resolution": ResolutionResult(
                            action="skip",
                            existing_content_id=content_id,
                            confidence=resolution.confidence,
                            match_signals=resolution.match_signals + ["no_changes"],
                        ),
                    },
                    trace_id=message.trace_id,
                )

            logger.info(f"Content {content_id}: {len(changed_fields)} fields changed: {list(changed_fields.keys())}")

            return PipelineMessage(
                message_type=MessageType.CONFLICT_RESOLVED,
                job_id=message.job_id,
                connector_name=message.connector_name,
                external_id=message.external_id,
                entity_type=message.entity_type,
                payload=normalized,
                raw_payload_id=message.raw_payload_id,
                metadata={**message.metadata, "changed_fields": changed_fields},
                trace_id=message.trace_id,
            )
        except Exception as e:
            logger.exception(f"Conflict resolution failed for {message.external_id}: {e}")
            return PipelineMessage(
                message_type=MessageType.FAILED,
                job_id=message.job_id,
                connector_name=message.connector_name,
                external_id=message.external_id,
                entity_type=message.entity_type,
                payload=message.payload,
                raw_payload_id=message.raw_payload_id,
                error=f"conflict_resolution: {str(e)}",
                metadata={**message.metadata, "failure_stage": "conflict_resolution"},
                trace_id=message.trace_id,
            )

    def _compute_diff(self, content_id: int, normalized: NormalizedContentDTO) -> Dict[str, Tuple[Any, Any]]:
        """Compare normalized data against existing catalog data.
        
        Returns dict of {field_name: (old_value, new_value)} for changed fields.
        Applies merge rules:
        - Completeness wins: empty → non-empty is always accepted
        - Never downgrade: non-zero rating → zero is rejected
        """
        changed: Dict[str, Tuple[Any, Any]] = {}

        with self._repo.get_session() as session:
            content = session.query(Content).filter(Content.id == content_id).first()
            if not content:
                return changed

            meta = content.metadata_rel
            art = content.artwork_rel
            stats = content.statistics_rel

            # --- Metadata fields ---
            if meta:
                self._compare_field(changed, "title", meta.title, normalized.title)
                self._compare_field(changed, "original_title", meta.original_title, normalized.original_title)
                self._compare_completeness(changed, "overview", meta.overview, normalized.overview)
                self._compare_completeness(changed, "tagline", meta.tagline, normalized.tagline)
                self._compare_field(changed, "release_date", meta.release_date, normalized.release_date)
                self._compare_field(changed, "runtime", meta.runtime, normalized.runtime)
                self._compare_field(changed, "language", meta.language, normalized.language)

            # --- Artwork fields ---
            if art:
                self._compare_completeness(changed, "poster_url", art.poster_url, normalized.poster_url)
                self._compare_completeness(changed, "backdrop_url", art.backdrop_url, normalized.backdrop_url)

            # --- Statistics fields (never downgrade) ---
            if stats:
                self._compare_no_downgrade(changed, "popularity", stats.popularity, normalized.popularity)
                self._compare_no_downgrade(changed, "average_rating", stats.average_rating, normalized.average_rating)
                self._compare_field(changed, "vote_count", stats.vote_count, normalized.vote_count)

        return changed

    @staticmethod
    def _compare_field(changed: dict, field: str, old_val: Any, new_val: Any):
        """Standard comparison — new value overwrites if different and not None."""
        if new_val is not None and str(old_val) != str(new_val):
            changed[field] = (old_val, new_val)

    @staticmethod
    def _compare_completeness(changed: dict, field: str, old_val: Any, new_val: Any):
        """Completeness wins — only overwrite if new is non-empty."""
        if new_val and str(new_val).strip():
            if not old_val or not str(old_val).strip() or str(old_val) != str(new_val):
                changed[field] = (old_val, new_val)

    @staticmethod
    def _compare_no_downgrade(changed: dict, field: str, old_val: Any, new_val: Any):
        """Never downgrade — don't replace a valid value with zero/None."""
        if new_val is not None and new_val != 0.0:
            old_num = float(old_val or 0.0)
            new_num = float(new_val)
            if old_num != new_num:
                changed[field] = (old_val, new_val)
