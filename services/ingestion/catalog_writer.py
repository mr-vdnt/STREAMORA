"""
DAP Catalog Writer — Executes Canonical Commands against the canonical catalog database.

CatalogWriter is the ONLY service permitted to write to catalog tables.
"""
from __future__ import annotations
import json
import logging
import uuid as uuid_lib
from datetime import datetime
from typing import Optional, List

from services.ingestion.contracts import PipelineStage, PipelineMessage, MessageType
from services.ingestion.commands import (
    CreateContentCommand, UpdateContentCommand, MergeContentCommand, DeleteContentCommand
)
from services.ingestion.dtos import NormalizedContentDTO, ResolutionResult, PipelineResult
from services.repository.catalog_db import (
    CatalogRepository, Content, ContentMetadata, ContentArtwork, ContentStatistics,
    ExternalIdentifier, Person, ContentPerson, Genre, ContentGenre,
    Season, Episode, OutboxEvent, IngestionProvenance, RawPayload
)

logger = logging.getLogger("streamora.ingestion.catalog_writer")


class CatalogWriter(PipelineStage):
    """Executes Canonical Commands and implements PipelineStage.
    
    Consumes: QUALITY_SCORED messages
    Emits: WRITTEN messages (payload is PipelineResult)
    """

    def __init__(self, catalog_repo: CatalogRepository = None):
        self._repo = catalog_repo or CatalogRepository()

    @property
    def stage_name(self) -> str:
        return "catalog_writer"

    async def process(self, message: PipelineMessage) -> PipelineMessage:
        resolution: ResolutionResult = message.metadata.get("resolution")
        normalized: NormalizedContentDTO = message.payload
        changed_fields = message.metadata.get("changed_fields", {})
        quality_report = message.metadata.get("quality_report")
        quality_score = quality_report.score if quality_report else 0.0

        if not resolution:
            return self._fail(message, "Missing resolution in metadata")

        try:
            if resolution.action == "create":
                cmd = CreateContentCommand(
                    normalized=normalized,
                    source_connector=message.connector_name,
                    raw_payload_id=message.raw_payload_id,
                    job_id=message.job_id,
                )
                result = self.execute_create(cmd, quality_score=quality_score)

            elif resolution.action == "update":
                cmd = UpdateContentCommand(
                    content_id=resolution.existing_content_id,
                    normalized=normalized,
                    changed_fields=changed_fields,
                    source_connector=message.connector_name,
                    raw_payload_id=message.raw_payload_id,
                    job_id=message.job_id,
                )
                result = self.execute_update(cmd, quality_score=quality_score)

            elif resolution.action == "skip":
                result = PipelineResult(
                    success=True,
                    action="skipped",
                    content_id=resolution.existing_content_id,
                    quality_score=quality_score,
                )
            else:
                return self._fail(message, f"Unknown resolution action: {resolution.action}")

            return PipelineMessage(
                message_type=MessageType.WRITTEN,
                job_id=message.job_id,
                connector_name=message.connector_name,
                external_id=message.external_id,
                entity_type=message.entity_type,
                payload=result,
                raw_payload_id=message.raw_payload_id,
                metadata={**message.metadata, "pipeline_result": result},
                trace_id=message.trace_id,
            )

        except Exception as e:
            logger.exception(f"Catalog write failed for {message.external_id}: {e}")
            return self._fail(message, f"catalog_writer: {str(e)}")

    def _fail(self, message: PipelineMessage, error: str) -> PipelineMessage:
        return PipelineMessage(
            message_type=MessageType.FAILED,
            job_id=message.job_id,
            connector_name=message.connector_name,
            external_id=message.external_id,
            entity_type=message.entity_type,
            payload=message.payload,
            raw_payload_id=message.raw_payload_id,
            error=error,
            metadata={**message.metadata, "failure_stage": "catalog_writer"},
            trace_id=message.trace_id,
        )

    # --- Command Execution Methods ---

    def execute_create(self, cmd: CreateContentCommand, quality_score: float = 0.0) -> PipelineResult:
        """Execute CreateContentCommand in a single atomic transaction."""
        norm = cmd.normalized
        content_uuid = str(uuid_lib.uuid4())
        with self._repo.get_session() as session:
            slug = self._generate_slug(norm.title, norm.release_date, session=session)

            # 1. Base Content aggregate root
            content = Content(
                uuid=content_uuid,
                slug=slug,
                entity_type=norm.entity_type,
                status="published",
            )
            session.add(content)
            session.flush()  # Generate content.id

            content_id = content.id

            # 2. Metadata
            meta = ContentMetadata(
                content_id=content_id,
                title=norm.title,
                original_title=norm.original_title or norm.title,
                overview=norm.overview,
                tagline=norm.tagline,
                release_date=norm.release_date,
                runtime=norm.runtime,
                language=norm.language,
            )
            session.add(meta)

            # 3. Artwork
            art = ContentArtwork(
                content_id=content_id,
                poster_url=norm.poster_url,
                backdrop_url=norm.backdrop_url,
            )
            session.add(art)

            # 4. Statistics
            stats = ContentStatistics(
                content_id=content_id,
                popularity=norm.popularity,
                average_rating=norm.average_rating,
                vote_count=norm.vote_count,
            )
            session.add(stats)

            # 5. External Identifiers
            for provider, ext_id in norm.external_ids.items():
                existing_ext = session.query(ExternalIdentifier).filter(
                    ExternalIdentifier.provider_name == provider,
                    ExternalIdentifier.external_id == str(ext_id)
                ).first()
                if not existing_ext:
                    ext = ExternalIdentifier(
                        content_id=content_id,
                        provider_name=provider,
                        external_id=str(ext_id),
                    )
                    session.add(ext)
                else:
                    existing_ext.content_id = content_id

            # 6. Genres & ContentGenre joins
            for genre_name in norm.genres:
                g = session.query(Genre).filter(Genre.name == genre_name).first()
                if not g:
                    g = Genre(name=genre_name, slug=self._generate_slug(genre_name))
                    session.add(g)
                    session.flush()
                cg = ContentGenre(content_id=content_id, genre_id=g.id)
                session.add(cg)

            # 7. Cast & Crew
            self._write_people(session, content_id, norm.cast + norm.crew)

            # 8. Seasons & Episodes (for TV Series)
            if norm.seasons:
                self._write_seasons(session, content_id, norm.seasons)

            # 9. Ingestion Provenance record
            prov = IngestionProvenance(
                content_id=content_id,
                connector_name=cmd.source_connector,
                raw_payload_id=cmd.raw_payload_id,
                job_id=cmd.job_id,
                quality_score=quality_score,
            )
            session.add(prov)

            # 10. Outbox Event
            event = OutboxEvent(
                aggregate_type="Content",
                aggregate_id=str(content_id),
                event_type="content.created",
                payload=json.dumps({
                    "content_id": content_id,
                    "uuid": content_uuid,
                    "slug": slug,
                    "entity_type": norm.entity_type,
                    "title": norm.title,
                    "source": cmd.source_connector,
                }),
            )
            session.add(event)

            session.commit()

            logger.info(f"Created Content #{content_id} ({slug}) via command from {cmd.source_connector}")

            return PipelineResult(
                success=True,
                action="created",
                content_id=content_id,
                content_uuid=content_uuid,
                quality_score=quality_score,
            )

    def execute_update(self, cmd: UpdateContentCommand, quality_score: float = 0.0) -> PipelineResult:
        """Execute UpdateContentCommand in a single atomic transaction."""
        norm = cmd.normalized
        content_id = cmd.content_id

        with self._repo.get_session() as session:
            content = session.query(Content).filter(Content.id == content_id).first()
            if not content:
                raise ValueError(f"Content #{content_id} not found")

            # Update content version and timestamp
            content.version_number += 1
            content.updated_at = datetime.utcnow()

            # Update metadata
            meta = session.query(ContentMetadata).filter(ContentMetadata.content_id == content_id).first()
            if meta:
                if "title" in cmd.changed_fields:
                    meta.title = norm.title
                if "overview" in cmd.changed_fields:
                    meta.overview = norm.overview
                if "release_date" in cmd.changed_fields:
                    meta.release_date = norm.release_date
                if "runtime" in cmd.changed_fields:
                    meta.runtime = norm.runtime

            # Update artwork
            art = session.query(ContentArtwork).filter(ContentArtwork.content_id == content_id).first()
            if art:
                if "poster_url" in cmd.changed_fields:
                    art.poster_url = norm.poster_url
                if "backdrop_url" in cmd.changed_fields:
                    art.backdrop_url = norm.backdrop_url

            # Update statistics
            stats = session.query(ContentStatistics).filter(ContentStatistics.content_id == content_id).first()
            if stats:
                if "popularity" in cmd.changed_fields:
                    stats.popularity = norm.popularity
                if "average_rating" in cmd.changed_fields:
                    stats.average_rating = norm.average_rating
                if "vote_count" in cmd.changed_fields:
                    stats.vote_count = norm.vote_count

            # Ensure new external IDs are recorded
            for provider, ext_id in norm.external_ids.items():
                existing_ext = session.query(ExternalIdentifier).filter(
                    ExternalIdentifier.content_id == content_id,
                    ExternalIdentifier.provider_name == provider
                ).first()
                if not existing_ext:
                    session.add(ExternalIdentifier(
                        content_id=content_id,
                        provider_name=provider,
                        external_id=str(ext_id),
                    ))

            # Update provenance
            prov = IngestionProvenance(
                content_id=content_id,
                connector_name=cmd.source_connector,
                raw_payload_id=cmd.raw_payload_id,
                job_id=cmd.job_id,
                quality_score=quality_score,
            )
            session.add(prov)

            # Outbox Event
            event = OutboxEvent(
                aggregate_type="Content",
                aggregate_id=str(content_id),
                event_type="content.updated",
                payload=json.dumps({
                    "content_id": content_id,
                    "uuid": content.uuid,
                    "changed_fields": list(cmd.changed_fields.keys()),
                    "source": cmd.source_connector,
                }),
            )
            session.add(event)

            session.commit()

            logger.info(f"Updated Content #{content_id} ({len(cmd.changed_fields)} fields) via command")

            return PipelineResult(
                success=True,
                action="updated",
                content_id=content_id,
                content_uuid=content.uuid,
                quality_score=quality_score,
            )

    def execute_merge(self, cmd: MergeContentCommand) -> PipelineResult:
        """Merge duplicate content into primary entity."""
        with self._repo.get_session() as session:
            primary = session.query(Content).filter(Content.id == cmd.primary_content_id).first()
            duplicate = session.query(Content).filter(Content.id == cmd.duplicate_content_id).first()

            if not primary or not duplicate:
                raise ValueError("Primary or duplicate content entity not found")

            # Re-point external identifiers
            dup_exts = session.query(ExternalIdentifier).filter(
                ExternalIdentifier.content_id == cmd.duplicate_content_id
            ).all()
            for ext in dup_exts:
                # Only re-point if primary doesn't already have this provider
                existing = session.query(ExternalIdentifier).filter(
                    ExternalIdentifier.content_id == cmd.primary_content_id,
                    ExternalIdentifier.provider_name == ext.provider_name
                ).first()
                if not existing:
                    ext.content_id = cmd.primary_content_id
                else:
                    session.delete(ext)

            # Soft delete duplicate
            duplicate.is_deleted = True
            duplicate.status = "merged"

            # Outbox event
            event = OutboxEvent(
                aggregate_type="Content",
                aggregate_id=str(cmd.primary_content_id),
                event_type="content.merged",
                payload=json.dumps({
                    "primary_content_id": cmd.primary_content_id,
                    "merged_content_id": cmd.duplicate_content_id,
                    "strategy": cmd.merge_strategy,
                }),
            )
            session.add(event)
            session.commit()

            return PipelineResult(
                success=True,
                action="merged",
                content_id=cmd.primary_content_id,
            )

    def execute_delete(self, cmd: DeleteContentCommand) -> PipelineResult:
        """Soft delete a content entity."""
        with self._repo.get_session() as session:
            content = session.query(Content).filter(Content.id == cmd.content_id).first()
            if not content:
                raise ValueError(f"Content #{cmd.content_id} not found")

            content.is_deleted = True
            content.status = "archived"

            event = OutboxEvent(
                aggregate_type="Content",
                aggregate_id=str(cmd.content_id),
                event_type="content.deleted",
                payload=json.dumps({
                    "content_id": cmd.content_id,
                    "reason": cmd.reason,
                    "actor": cmd.actor,
                }),
            )
            session.add(event)
            session.commit()

            return PipelineResult(
                success=True,
                action="deleted",
                content_id=cmd.content_id,
            )

    # --- Internal Helpers ---

    def _write_people(self, session, content_id: int, people: list):
        for p in people:
            person = session.query(Person).filter(Person.name == p.name).first()
            if not person:
                person = Person(name=p.name, profile_url=p.profile_url)
                session.add(person)
                session.flush()
            cp = ContentPerson(
                content_id=content_id,
                person_id=person.id,
                role=p.role,
                character_name=p.character_name,
                display_order=p.order,
            )
            session.add(cp)

    def _write_seasons(self, session, content_id: int, seasons: list):
        for s in seasons:
            season = Season(
                content_id=content_id,
                season_number=s.season_number,
                title=s.title,
                overview=s.overview,
                poster_url=s.poster_url,
                air_date=s.air_date,
            )
            session.add(season)
            session.flush()

            for ep in s.episodes:
                episode = Episode(
                    season_id=season.id,
                    episode_number=ep.episode_number,
                    title=ep.title,
                    overview=ep.overview,
                    still_url=ep.still_url,
                    runtime=ep.runtime,
                    rating=ep.rating,
                    air_date=ep.air_date,
                )
                session.add(episode)

    def _generate_slug(self, title: str, date_str: Optional[str] = None, session=None) -> str:
        base = "".join(c.lower() if c.isalnum() else "-" for c in title).strip("-")
        while "--" in base:
            base = base.replace("--", "-")
        if date_str and len(date_str) >= 4:
            year = date_str[:4]
            slug = f"{base}-{year}"
        else:
            slug = base

        if session:
            existing = session.query(Content).filter(Content.slug == slug).first()
            if existing:
                counter = 1
                while session.query(Content).filter(Content.slug == f"{slug}-{counter}").first():
                    counter += 1
                slug = f"{slug}-{counter}"

        return slug
