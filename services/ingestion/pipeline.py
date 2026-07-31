"""
DAP Pipeline Orchestrator — Wires together the message-driven ingestion pipeline.
"""
from __future__ import annotations
import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from services.ingestion.contracts import (
    PipelineMessage, MessageType, BaseConnector
)
from services.ingestion.dtos import RawPayloadDTO, PipelineResult
from services.ingestion.message_bus import InProcessMessageBus
from services.ingestion.stages.validator import ValidatorStage
from services.ingestion.stages.normalizer import NormalizerStage
from services.ingestion.stages.resolver import EntityResolverStage
from services.ingestion.stages.conflict_resolver import ConflictResolverStage
from services.ingestion.stages.quality_scorer import QualityScorerStage
from services.ingestion.catalog_writer import CatalogWriter
from services.repository.catalog_db import (
    CatalogRepository, IngestionJob, RawPayload, DeadLetterRecord
)

logger = logging.getLogger("streamora.ingestion.pipeline")


class DataAcquisitionPipeline:
    """Message-driven Data Acquisition Platform (DAP) Pipeline.
    
    Orchestrates ingestion flow across message-oriented stages:
    
    Connector -> Raw Payload (DB) -> Validator -> Normalizer -> Entity Resolver
             -> Conflict Resolver -> Quality Scorer -> Catalog Writer (Commands) -> Outbox
    """

    def __init__(self, catalog_repo: CatalogRepository = None):
        self._repo = catalog_repo or CatalogRepository()
        self.bus = InProcessMessageBus()
        self.catalog_writer = CatalogWriter(self._repo)

        # Wire pipeline stages
        self._setup_pipeline()

    def _setup_pipeline(self):
        """Register stages in sequential order on the message bus."""
        validator = ValidatorStage()
        normalizer = NormalizerStage()
        resolver = EntityResolverStage(self._repo)
        conflict_resolver = ConflictResolverStage(self._repo)
        scorer = QualityScorerStage()

        self.bus.register(MessageType.RAW_PAYLOAD, validator)
        self.bus.register(MessageType.VALIDATED, normalizer)
        self.bus.register(MessageType.NORMALIZED, resolver)
        self.bus.register(MessageType.RESOLVED, conflict_resolver)
        self.bus.register(MessageType.CONFLICT_RESOLVED, scorer)
        self.bus.register(MessageType.QUALITY_SCORED, self.catalog_writer)

        self.bus.set_dead_letter_handler(self._handle_dead_letter)

    async def process_raw_payload(
        self,
        raw_dto: RawPayloadDTO,
        job_id: Optional[int] = None
    ) -> PipelineResult:
        """Process a single RawPayloadDTO through the full pipeline."""

        # 1. Compute payload hash
        payload_str = json.dumps(raw_dto.raw_data, sort_keys=True)
        payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

        # 2. Persist RawPayload to DB (immutable audit record)
        raw_payload_id = self._persist_raw_payload(
            job_id=job_id or 0,
            connector_name=raw_dto.connector_name,
            external_id=raw_dto.external_id,
            entity_type=raw_dto.entity_type,
            payload_json=payload_str,
            payload_hash=payload_hash,
        )

        # 3. Create initial PipelineMessage
        init_message = PipelineMessage(
            message_type=MessageType.RAW_PAYLOAD,
            job_id=job_id or 0,
            connector_name=raw_dto.connector_name,
            external_id=raw_dto.external_id,
            entity_type=raw_dto.entity_type,
            payload=raw_dto.raw_data,
            raw_payload_id=raw_payload_id,
            metadata={"payload_hash": payload_hash},
        )

        # 4. Publish message through pipeline
        final_message = await self.bus.publish(init_message)

        if final_message and final_message.message_type == MessageType.WRITTEN:
            return final_message.payload  # PipelineResult
        elif final_message and final_message.message_type == MessageType.FAILED:
            return PipelineResult(
                success=False,
                action="failed",
                errors=[final_message.error or "Pipeline failed"],
            )
        else:
            return PipelineResult(
                success=False,
                action="failed",
                errors=["Pipeline produced unknown output state"],
            )

    async def run_job(
        self,
        connector: BaseConnector,
        job_type: str = "on_demand",
        entity_type: str = "movie",
        limit: int = 20
    ) -> IngestionJobReport:
        """Execute a full ingestion job for a connector."""
        manifest = connector.get_manifest()

        # 1. Create IngestionJob record
        job_id = self._create_job(manifest.name, job_type)

        report = IngestionJobReport(job_id=job_id, connector_name=manifest.name)

        try:
            # 2. Fetch payloads from connector
            logger.info(f"Starting ingestion job #{job_id} for {manifest.name} ({entity_type})")
            payloads = await connector.fetch_trending(entity_type=entity_type)
            report.items_fetched = len(payloads[:limit])

            # 3. Process each payload through pipeline
            for raw_dto in payloads[:limit]:
                result = await self.process_raw_payload(raw_dto, job_id=job_id)

                if result.success:
                    if result.action == "created":
                        report.items_created += 1
                    elif result.action == "updated":
                        report.items_updated += 1
                    elif result.action == "skipped":
                        report.items_skipped += 1
                else:
                    report.items_failed += 1

            # 4. Complete job record
            self._update_job_status(job_id, "completed", report)
            logger.info(
                f"Completed job #{job_id}: {report.items_created} created, "
                f"{report.items_updated} updated, {report.items_skipped} skipped, "
                f"{report.items_failed} failed"
            )

        except Exception as e:
            logger.exception(f"Job #{job_id} failed: {e}")
            report.error_summary = str(e)
            self._update_job_status(job_id, "failed", report)

        return report

    # --- DB Helpers ---

    def _persist_raw_payload(self, job_id: int, connector_name: str, external_id: str, entity_type: str, payload_json: str, payload_hash: str) -> int:
        with self._repo.get_session() as session:
            raw = RawPayload(
                job_id=job_id,
                connector_name=connector_name,
                external_id=external_id,
                entity_type=entity_type,
                payload_json=payload_json,
                payload_hash=payload_hash,
            )
            session.add(raw)
            session.commit()
            return raw.id

    def _create_job(self, connector_name: str, job_type: str) -> int:
        with self._repo.get_session() as session:
            job = IngestionJob(
                connector_name=connector_name,
                job_type=job_type,
                status="running",
                started_at=datetime.utcnow(),
            )
            session.add(job)
            session.commit()
            return job.id

    def _update_job_status(self, job_id: int, status: str, report: IngestionJobReport):
        with self._repo.get_session() as session:
            job = session.query(IngestionJob).filter(IngestionJob.id == job_id).first()
            if job:
                job.status = status
                job.completed_at = datetime.utcnow()
                job.items_fetched = report.items_fetched
                job.items_ingested = report.items_created + report.items_updated
                job.items_skipped = report.items_skipped
                job.items_failed = report.items_failed
                job.error_summary = report.error_summary
                session.commit()

    def _handle_dead_letter(self, message: PipelineMessage):
        """Dead letter handler — records failed messages to dead_letter_records table."""
        try:
            with self._repo.get_session() as session:
                payload_str = json.dumps(message.payload) if isinstance(message.payload, dict) else str(message.payload)
                dlr = DeadLetterRecord(
                    job_id=message.job_id,
                    connector_name=message.connector_name,
                    external_id=message.external_id,
                    payload_json=payload_str,
                    failure_stage=message.metadata.get("failure_stage", "unknown"),
                    failure_reason=message.error or "Unknown failure",
                )
                session.add(dlr)
                session.commit()
                logger.info(f"Recorded dead letter for {message.external_id} ({message.connector_name})")
        except Exception as e:
            logger.error(f"Failed to record dead letter: {e}")


class IngestionJobReport:
    """Summary report for an ingestion job run."""

    def __init__(self, job_id: int, connector_name: str):
        self.job_id = job_id
        self.connector_name = connector_name
        self.items_fetched = 0
        self.items_created = 0
        self.items_updated = 0
        self.items_skipped = 0
        self.items_failed = 0
        self.error_summary: Optional[str] = None
