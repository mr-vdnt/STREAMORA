"""
DAP Entity Resolver Stage — Multi-signal duplicate detection and entity resolution.
"""
from __future__ import annotations
import logging
from services.ingestion.contracts import PipelineStage, PipelineMessage, MessageType
from services.ingestion.dtos import NormalizedContentDTO, ResolutionResult
from services.repository.catalog_db import CatalogRepository, ExternalIdentifier, Content, ContentMetadata

logger = logging.getLogger("streamora.ingestion.resolver")


class EntityResolverStage(PipelineStage):
    """Resolves whether a normalized content item is new, existing, or a duplicate.
    
    Consumes: NORMALIZED messages (NormalizedContentDTO as payload)
    Emits: RESOLVED messages (payload is enriched with ResolutionResult in metadata)
    
    Resolution signals (ordered by confidence):
    1. ExternalIdentifier match (confidence: 1.0)
    2. Title + Year exact match (confidence: 0.9)
    3. Title fuzzy match + same entity_type (confidence: 0.7)
    """

    def __init__(self, catalog_repo: CatalogRepository = None):
        self._repo = catalog_repo or CatalogRepository()

    @property
    def stage_name(self) -> str:
        return "entity_resolver"

    async def process(self, message: PipelineMessage) -> PipelineMessage:
        normalized: NormalizedContentDTO = message.payload

        try:
            resolution = self._resolve(normalized)

            return PipelineMessage(
                message_type=MessageType.RESOLVED,
                job_id=message.job_id,
                connector_name=message.connector_name,
                external_id=message.external_id,
                entity_type=message.entity_type,
                payload=normalized,
                raw_payload_id=message.raw_payload_id,
                metadata={
                    **message.metadata,
                    "resolution": resolution,
                },
                trace_id=message.trace_id,
            )
        except Exception as e:
            logger.exception(f"Entity resolution failed for {message.external_id}: {e}")
            return PipelineMessage(
                message_type=MessageType.FAILED,
                job_id=message.job_id,
                connector_name=message.connector_name,
                external_id=message.external_id,
                entity_type=message.entity_type,
                payload=message.payload,
                raw_payload_id=message.raw_payload_id,
                error=f"resolution: {str(e)}",
                metadata={**message.metadata, "failure_stage": "resolution"},
                trace_id=message.trace_id,
            )

    def _resolve(self, normalized: NormalizedContentDTO) -> ResolutionResult:
        """Multi-signal entity resolution."""
        with self._repo.get_session() as session:
            # Signal 1: Canonical IMDb ExternalIdentifier match (highest confidence)
            imdb_id = normalized.external_ids.get("imdb")
            if imdb_id:
                clean_imdb_id = imdb_id if str(imdb_id).startswith("tt") else f"tt{imdb_id}"
                existing_imdb = session.query(ExternalIdentifier).filter(
                    ExternalIdentifier.provider_name == "imdb",
                    ExternalIdentifier.external_id == clean_imdb_id
                ).first()
                if existing_imdb:
                    return ResolutionResult(
                        action="update",
                        existing_content_id=existing_imdb.content_id,
                        confidence=1.0,
                        match_signals=[f"external_id:imdb={clean_imdb_id}"],
                    )

            # Signal 1b: Provider ExternalIdentifier match
            for provider, ext_id in normalized.external_ids.items():
                if provider == "imdb":
                    continue
                existing = session.query(ExternalIdentifier).filter(
                    ExternalIdentifier.provider_name == provider,
                    ExternalIdentifier.external_id == str(ext_id)
                ).first()

                if existing:
                    return ResolutionResult(
                        action="update",
                        existing_content_id=existing.content_id,
                        confidence=1.0,
                        match_signals=[f"external_id:{provider}={ext_id}"],
                    )

            # Signal 2: Title + Year exact match
            release_date = normalized.release_date or ""
            year = release_date[:4] if len(release_date) >= 4 else ""

            if normalized.title and year:
                meta_matches = session.query(ContentMetadata).filter(
                    ContentMetadata.title == normalized.title
                ).all()

                for meta in meta_matches:
                    meta_year = (meta.release_date or "")[:4]
                    if meta_year == year:
                        # Verify entity type matches
                        content = session.query(Content).filter(
                            Content.id == meta.content_id,
                            Content.is_deleted == False,
                        ).first()
                        if content and content.entity_type == normalized.entity_type:
                            return ResolutionResult(
                                action="update",
                                existing_content_id=content.id,
                                confidence=0.9,
                                match_signals=[f"title_year:{normalized.title}:{year}"],
                            )

            # Signal 3: Title case-insensitive + same entity type
            if normalized.title:
                meta_matches = session.query(ContentMetadata).filter(
                    ContentMetadata.title.ilike(normalized.title)
                ).all()

                for meta in meta_matches:
                    content = session.query(Content).filter(
                        Content.id == meta.content_id,
                        Content.entity_type == normalized.entity_type,
                        Content.is_deleted == False,
                    ).first()
                    if content:
                        return ResolutionResult(
                            action="update",
                            existing_content_id=content.id,
                            confidence=0.7,
                            match_signals=[f"title_fuzzy:{normalized.title}"],
                        )

            # No match found — create new
            return ResolutionResult(
                action="create",
                existing_content_id=None,
                confidence=0.0,
                match_signals=[],
            )
