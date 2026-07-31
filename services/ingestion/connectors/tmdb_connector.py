"""
TMDB Connector — Fetches raw metadata from the TMDb (The Movie Database) API.
Implements BaseConnector.
"""
from __future__ import annotations
import hashlib
import json
import logging
from datetime import datetime
from typing import List, Optional

import httpx
from core.config import settings
from services.ingestion.contracts import (
    BaseConnector, ConnectorManifest, ConnectorCapability
)
from services.ingestion.dtos import RawPayloadDTO

logger = logging.getLogger("streamora.ingestion.connectors.tmdb")

TMDB_API_BASE = "https://api.themoviedb.org/3"


class TMDBConnector(BaseConnector):
    """Data connector for TMDB (The Movie Database) API v3."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings.tmdb, "api_key", None)
        self.client = httpx.AsyncClient(timeout=15.0)

    def get_manifest(self) -> ConnectorManifest:
        return ConnectorManifest(
            name="tmdb",
            display_name="The Movie Database",
            capabilities=[
                ConnectorCapability.SEARCH,
                ConnectorCapability.FETCH_BY_ID,
                ConnectorCapability.TRENDING,
                ConnectorCapability.CHANGES,
            ],
            rate_limit_per_second=getattr(settings.ingestion, "tmdb_rate_limit_per_second", 4.0),
            supported_entity_types=["movie", "tvseries"],
        )

    async def fetch_by_id(self, external_id: str, entity_type: str = "movie") -> Optional[RawPayloadDTO]:
        """Fetch full details for a movie or TV series including credits and images."""
        if not self.api_key:
            logger.error("TMDB API key not configured")
            return None

        endpoint_type = "movie" if entity_type == "movie" else "tv"
        url = f"{TMDB_API_BASE}/{endpoint_type}/{external_id}"
        params = {
            "api_key": self.api_key,
            "append_to_response": "credits,images,external_ids",
        }

        try:
            resp = await self.client.get(url, params=params)
            if resp.status_code == 404:
                logger.warning(f"TMDB ID {external_id} not found ({entity_type})")
                return None
            resp.raise_for_status()

            raw_json = resp.json()
            return self._build_raw_payload(external_id, entity_type, raw_json)

        except Exception as e:
            logger.error(f"Failed to fetch TMDB ID {external_id}: {e}")
            return None

    async def fetch_trending(self, entity_type: str = "movie", page: int = 1) -> List[RawPayloadDTO]:
        """Fetch trending movies or TV series for the day."""
        if not self.api_key:
            return []

        media_type = "movie" if entity_type == "movie" else "tv"
        url = f"{TMDB_API_BASE}/trending/{media_type}/day"
        params = {"api_key": self.api_key, "page": page}

        try:
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
            results = resp.json().get("results", [])

            payloads = []
            for item in results:
                ext_id = str(item.get("id"))
                payloads.append(self._build_raw_payload(ext_id, entity_type, item))
            return payloads

        except Exception as e:
            logger.error(f"Failed to fetch TMDB trending ({entity_type}): {e}")
            return []

    async def search(self, query: str, entity_type: str = "movie") -> List[RawPayloadDTO]:
        """Search TMDB by query string."""
        if not self.api_key:
            return []

        media_type = "movie" if entity_type == "movie" else "tv"
        url = f"{TMDB_API_BASE}/search/{media_type}"
        params = {"api_key": self.api_key, "query": query, "page": 1}

        try:
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
            results = resp.json().get("results", [])

            payloads = []
            for item in results:
                ext_id = str(item.get("id"))
                payloads.append(self._build_raw_payload(ext_id, entity_type, item))
            return payloads

        except Exception as e:
            logger.error(f"Failed to search TMDB query '{query}': {e}")
            return []

    async def fetch_changes(self, since: datetime) -> List[RawPayloadDTO]:
        """Fetch IDs of items changed since timestamp."""
        if not self.api_key:
            return []

        date_str = since.strftime("%Y-%m-%d")
        url = f"{TMDB_API_BASE}/movie/changes"
        params = {"api_key": self.api_key, "start_date": date_str}

        try:
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
            results = resp.json().get("results", [])

            # Fetch full payload for each changed item (up to 20)
            payloads = []
            for item in results[:20]:
                ext_id = str(item.get("id"))
                payload = await self.fetch_by_id(ext_id, "movie")
                if payload:
                    payloads.append(payload)
            return payloads

        except Exception as e:
            logger.error(f"Failed to fetch TMDB changes since {date_str}: {e}")
            return []

    def _build_raw_payload(self, external_id: str, entity_type: str, raw_json: dict) -> RawPayloadDTO:
        return RawPayloadDTO(
            connector_name="tmdb",
            external_id=external_id,
            entity_type=entity_type,
            raw_data=raw_json,
            fetched_at=datetime.utcnow(),
        )

    async def close(self):
        await self.client.aclose()
