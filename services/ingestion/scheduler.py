"""
DAP Sync Scheduler — Manages automated recurring ingestion sync jobs.
"""
from __future__ import annotations
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from core.config import settings
from services.ingestion.contracts import BaseConnector
from services.ingestion.pipeline import DataAcquisitionPipeline, IngestionJobReport
from services.ingestion.connectors.tmdb_connector import TMDBConnector
from services.repository.catalog_db import CatalogRepository, SyncCheckpoint

logger = logging.getLogger("streamora.ingestion.scheduler")


class IngestionScheduler:
    """Manages scheduled background synchronization across registered connectors."""

    def __init__(self, pipeline: DataAcquisitionPipeline = None, catalog_repo: CatalogRepository = None):
        self._repo = catalog_repo or CatalogRepository()
        self.pipeline = pipeline or DataAcquisitionPipeline(self._repo)
        self._connectors: Dict[str, BaseConnector] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Register default TMDB connector if API key is set
        if getattr(settings.tmdb, "api_key", None):
            self.register_connector(TMDBConnector())

    def register_connector(self, connector: BaseConnector):
        manifest = connector.get_manifest()
        self._connectors[manifest.name] = connector
        logger.info(f"Registered connector '{manifest.name}' ({manifest.display_name}) with scheduler")

    async def trigger_sync(self, connector_name: str, entity_type: str = "movie", limit: int = 20) -> IngestionJobReport:
        """Trigger an immediate sync for a specific connector."""
        connector = self._connectors.get(connector_name)
        if not connector:
            raise ValueError(f"Connector '{connector_name}' is not registered")

        report = await self.pipeline.run_job(
            connector=connector,
            job_type="incremental",
            entity_type=entity_type,
            limit=limit,
        )

        # Update sync checkpoint
        self._update_checkpoint(connector_name, report.items_created + report.items_updated)
        return report

    def _update_checkpoint(self, connector_name: str, items_synced: int):
        with self._repo.get_session() as session:
            chk = session.query(SyncCheckpoint).filter(
                SyncCheckpoint.connector_name == connector_name
            ).first()
            if not chk:
                chk = SyncCheckpoint(
                    connector_name=connector_name,
                    last_sync_at=datetime.utcnow(),
                    items_synced=items_synced,
                )
                session.add(chk)
            else:
                chk.last_sync_at = datetime.utcnow()
                chk.items_synced += items_synced
            session.commit()

    async def start(self, interval_hours: int = None):
        """Start the background scheduler loop."""
        hours = interval_hours or getattr(settings.ingestion, "default_sync_interval_hours", 24)
        interval_seconds = hours * 3600

        self._running = True
        logger.info(f"Starting IngestionScheduler with interval of {hours} hours")

        while self._running:
            try:
                for name in self._connectors:
                    logger.info(f"Scheduler running sync for '{name}'")
                    await self.trigger_sync(name, entity_type="movie", limit=20)
                    await self.trigger_sync(name, entity_type="tvseries", limit=20)
            except Exception as e:
                logger.error(f"Error in scheduler sync run: {e}")

            await asyncio.sleep(interval_seconds)

    def stop(self):
        """Stop the background scheduler loop."""
        self._running = False
        if self._task:
            self._task.cancel()
        logger.info("IngestionScheduler stopped")
