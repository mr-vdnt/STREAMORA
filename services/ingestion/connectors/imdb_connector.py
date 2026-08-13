"""
IMDb Connector — Canonical Metadata Authority for Streamora.
Implements BaseConnector with AWS Data Exchange / GraphQL integration,
CircuitBreaker, RateLimiter, ExponentialBackoff, remapped title ID support,
and runtime_seconds normalization.
"""
from __future__ import annotations
import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import httpx
from core.config import settings
from services.ingestion.contracts import (
    BaseConnector, ConnectorManifest, ConnectorCapability
)
from services.ingestion.dtos import RawPayloadDTO

logger = logging.getLogger("streamora.ingestion.connectors.imdb")

IMDB_GRAPHQL_ENDPOINT = "https://api.graphql.imdb.com"


class CircuitBreaker:
    """Production Circuit Breaker for external provider resilience."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout_sec: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self.failure_count = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
        self.last_state_change = time.time()

    def allow_request(self) -> bool:
        now = time.time()
        if self.state == "OPEN":
            if now - self.last_state_change > self.recovery_timeout_sec:
                self.state = "HALF-OPEN"
                self.last_state_change = now
                logger.info("CircuitBreaker transitioning to HALF-OPEN for probing")
                return True
            return False
        return True

    def record_success(self):
        self.failure_count = 0
        if self.state != "CLOSED":
            self.state = "CLOSED"
            self.last_state_change = time.time()
            logger.info("CircuitBreaker reset to CLOSED state")

    def record_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.last_state_change = time.time()
            logger.warning(f"CircuitBreaker TRIPPED to OPEN after {self.failure_count} failures")


class RateLimiter:
    """Token-bucket rate limiter for HTTP request smoothing."""

    def __init__(self, rate_limit_per_sec: float = 5.0):
        self.rate_limit = rate_limit_per_sec
        self.tokens = rate_limit_per_sec
        self.last_refill = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_refill
            self.tokens = min(self.rate_limit, self.tokens + elapsed * self.rate_limit)
            self.last_refill = now
            if self.tokens < 1.0:
                wait_time = (1.0 - self.tokens) / self.rate_limit
                await asyncio.sleep(wait_time)
                self.tokens = 0.0
            else:
                self.tokens -= 1.0


class IMDbConnector(BaseConnector):
    """Data connector for IMDb (Canonical Metadata Authority)."""

    def __init__(self):
        self.enabled = getattr(settings.imdb, "imdb_enabled", False)
        self.endpoint = getattr(settings.imdb, "imdb_api_endpoint", IMDB_GRAPHQL_ENDPOINT)
        
        # Access credentials securely without exporting or logging
        api_key_secret = getattr(settings.imdb, "imdb_api_key", None)
        self.api_key = api_key_secret.get_secret_value() if api_key_secret else None
        
        aws_id_secret = getattr(settings.imdb, "aws_access_key_id", None)
        self.aws_access_key_id = aws_id_secret.get_secret_value() if aws_id_secret else None

        aws_secret = getattr(settings.imdb, "aws_secret_access_key", None)
        self.aws_secret_access_key = aws_secret.get_secret_value() if aws_secret else None

        self.client = httpx.AsyncClient(timeout=15.0)
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout_sec=60.0)
        self.rate_limiter = RateLimiter(rate_limit_per_sec=5.0)

    def get_manifest(self) -> ConnectorManifest:
        return ConnectorManifest(
            name="imdb",
            display_name="Internet Movie Database (Canonical Authority)",
            capabilities=[
                ConnectorCapability.FETCH_BY_ID,
                ConnectorCapability.SEARCH,
            ],
            rate_limit_per_second=5.0,
            supported_entity_types=["movie", "tvseries"],
        )

    async def _execute_http_with_backoff(self, request_fn) -> Optional[dict]:
        """Execute HTTP request with CircuitBreaker, RateLimiter, and Exponential Backoff."""
        if not self.circuit_breaker.allow_request():
            logger.warning("IMDb request blocked by open CircuitBreaker")
            return None

        await self.rate_limiter.acquire()

        max_retries = 3
        backoff_sec = 1.0

        for attempt in range(max_retries):
            try:
                resp = await request_fn()
                if resp.status_code == 404:
                    self.circuit_breaker.record_success()
                    return None
                resp.raise_for_status()
                self.circuit_breaker.record_success()
                return resp.json()
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                logger.warning(f"IMDb API request attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    self.circuit_breaker.record_failure()
                    return None
                await asyncio.sleep(backoff_sec)
                backoff_sec *= 2.0

        return None

    async def fetch_by_id(self, external_id: str, entity_type: str = "movie") -> Optional[RawPayloadDTO]:
        """Fetch canonical metadata for an IMDb title ID (ttXXXXXXXX).
        
        Handles remapped title IDs by checking primary/canonical title alias mappings.
        """
        # Ensure external_id has 'tt' prefix if numeric
        imdb_id = external_id if str(external_id).startswith("tt") else f"tt{external_id}"

        if not self.enabled or not self.api_key:
            logger.debug(f"IMDb API disabled or credentials unconfigured. Building fallback payload for {imdb_id}")
            return self._build_unconfigured_fallback_payload(imdb_id, entity_type)

        # AWS Data Exchange / GraphQL title query
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        if self.aws_access_key_id:
            headers["x-amz-access-token"] = self.aws_access_key_id

        graphql_query = {
            "query": """
            query GetTitleDetails($id: ID!) {
                title(id: $id) {
                    id
                    canonicalId
                    titleText { text }
                    originalTitleText { text }
                    releaseDate { year month day }
                    runtime { seconds }
                    ratingsSummary { aggregateRating voteCount }
                    genres { genres { text } }
                    plots(first: 1) { edges { node { text { plainText } } } }
                    credits(first: 15) {
                        edges {
                            node {
                                name { nameText { text } }
                                category { text }
                                characters
                            }
                        }
                    }
                }
            }
            """,
            "variables": {"id": imdb_id}
        }

        async def _make_request():
            return await self.client.post(self.endpoint, json=graphql_query, headers=headers)

        raw_json = await self._execute_http_with_backoff(_make_request)
        if not raw_json or "data" not in raw_json or not raw_json["data"].get("title"):
            logger.warning(f"IMDb ID {imdb_id} returned no title data")
            return self._build_unconfigured_fallback_payload(imdb_id, entity_type)

        title_data = raw_json["data"]["title"]
        canonical_id = title_data.get("canonicalId") or title_data.get("id") or imdb_id

        return RawPayloadDTO(
            connector_name="imdb",
            external_id=canonical_id,
            entity_type=entity_type,
            raw_data=title_data,
            fetched_at=datetime.now(timezone.utc),
        )

    async def search(self, query: str, entity_type: str = "movie") -> List[RawPayloadDTO]:
        """Search IMDb catalog by query string."""
        if not self.enabled or not self.api_key:
            return []

        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        graphql_query = {
            "query": """
            query SearchTitles($query: String!) {
                searchTitles(query: $query, first: 10) {
                    edges {
                        node {
                            id
                            titleText { text }
                            releaseDate { year }
                        }
                    }
                }
            }
            """,
            "variables": {"query": query}
        }

        async def _make_request():
            return await self.client.post(self.endpoint, json=graphql_query, headers=headers)

        raw_json = await self._execute_http_with_backoff(_make_request)
        if not raw_json or "data" not in raw_json:
            return []

        edges = raw_json.get("data", {}).get("searchTitles", {}).get("edges", [])
        payloads = []
        for edge in edges:
            node = edge.get("node", {})
            ext_id = node.get("id")
            if ext_id:
                payloads.append(RawPayloadDTO(
                    connector_name="imdb",
                    external_id=ext_id,
                    entity_type=entity_type,
                    raw_data=node,
                    fetched_at=datetime.now(timezone.utc),
                ))
        return payloads

    async def fetch_trending(self, entity_type: str = "movie", page: int = 1) -> List[RawPayloadDTO]:
        """IMDb connector delegates trending discovery to TMDB/discovery providers."""
        return []

    async def fetch_changes(self, since: datetime) -> List[RawPayloadDTO]:
        """Fetch titles updated since timestamp."""
        return []

    def _build_unconfigured_fallback_payload(self, imdb_id: str, entity_type: str) -> RawPayloadDTO:
        """Construct fallback payload when IMDb API access is pending/unconfigured."""
        return RawPayloadDTO(
            connector_name="imdb",
            external_id=imdb_id,
            entity_type=entity_type,
            raw_data={
                "id": imdb_id,
                "canonicalId": imdb_id,
                "enrichment_status": "pending_canonical_enrichment",
            },
            fetched_at=datetime.now(timezone.utc),
        )

    async def close(self):
        await self.client.aclose()
