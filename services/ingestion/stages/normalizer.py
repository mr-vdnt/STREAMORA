"""
DAP Normalizer Stage — Maps raw provider payloads to NormalizedContentDTO.
"""
from __future__ import annotations
import logging
from typing import Dict, List, Optional
from services.ingestion.contracts import PipelineStage, PipelineMessage, MessageType
from services.ingestion.dtos import (
    NormalizedContentDTO, PersonDTO, SeasonDTO, EpisodeDTO
)

logger = logging.getLogger("streamora.ingestion.normalizer")

TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/"


class NormalizerStage(PipelineStage):
    """Normalizes validated raw payloads into NormalizedContentDTO.
    
    Consumes: VALIDATED messages (raw_data dict as payload)
    Emits: NORMALIZED messages (NormalizedContentDTO as payload)
    
    Currently supports TMDB payload format. Future connectors
    should add their own normalization methods keyed by connector_name.
    """

    @property
    def stage_name(self) -> str:
        return "normalizer"

    async def process(self, message: PipelineMessage) -> PipelineMessage:
        raw_data = message.payload
        connector = message.connector_name

        try:
            if connector == "imdb":
                normalized = self._normalize_imdb(raw_data, message.entity_type)
            elif connector == "tmdb":
                normalized = self._normalize_tmdb(raw_data, message.entity_type)
            else:
                normalized = self._normalize_generic(raw_data, message.entity_type, connector)

            normalized.source_connector = connector
            normalized.source_payload_hash = message.metadata.get("payload_hash", "")

            return PipelineMessage(
                message_type=MessageType.NORMALIZED,
                job_id=message.job_id,
                connector_name=message.connector_name,
                external_id=message.external_id,
                entity_type=message.entity_type,
                payload=normalized,
                raw_payload_id=message.raw_payload_id,
                metadata=message.metadata,
                trace_id=message.trace_id,
            )
        except Exception as e:
            logger.exception(f"Normalization failed for {message.external_id}: {e}")
            return PipelineMessage(
                message_type=MessageType.FAILED,
                job_id=message.job_id,
                connector_name=message.connector_name,
                external_id=message.external_id,
                entity_type=message.entity_type,
                payload=message.payload,
                raw_payload_id=message.raw_payload_id,
                error=f"normalization: {str(e)}",
                metadata={**message.metadata, "failure_stage": "normalization"},
                trace_id=message.trace_id,
            )

    def _normalize_imdb(self, data: dict, entity_type: str) -> NormalizedContentDTO:
        """Normalize canonical IMDb API GraphQL / AWS Data Exchange response."""
        imdb_id = data.get("canonicalId") or data.get("id", "")
        if imdb_id and not str(imdb_id).startswith("tt"):
            imdb_id = f"tt{imdb_id}"

        title_text = data.get("titleText", {})
        title = title_text.get("text") if isinstance(title_text, dict) else (data.get("title") or "Untitled")

        orig_text = data.get("originalTitleText", {})
        original_title = orig_text.get("text") if isinstance(orig_text, dict) else title

        # Release date
        rel_date = data.get("releaseDate", {})
        release_date = ""
        if isinstance(rel_date, dict) and rel_date.get("year"):
            y = rel_date["year"]
            m = str(rel_date.get("month") or 1).zfill(2)
            d = str(rel_date.get("day") or 1).zfill(2)
            release_date = f"{y}-{m}-{d}"
        elif isinstance(data.get("release_date"), str):
            release_date = data["release_date"]

        # Runtime seconds
        runtime_sec = None
        if "runtime" in data and isinstance(data["runtime"], dict):
            runtime_sec = data["runtime"].get("seconds")
        elif isinstance(data.get("runtime_seconds"), int):
            runtime_sec = data["runtime_seconds"]
        elif isinstance(data.get("runtime"), int):
            runtime_sec = data["runtime"] * 60

        runtime_min = (runtime_sec // 60) if runtime_sec else None

        # Ratings
        ratings = data.get("ratingsSummary", {})
        imdb_rating = float(ratings.get("aggregateRating") or 0.0) if isinstance(ratings, dict) else float(data.get("imdb_rating") or 0.0)
        imdb_vote_count = int(ratings.get("voteCount") or 0) if isinstance(ratings, dict) else int(data.get("imdb_vote_count") or 0)

        # Genres
        genres_node = data.get("genres", {})
        raw_g_list = genres_node.get("genres", []) if isinstance(genres_node, dict) else data.get("genres", [])
        genres = [g.get("text") if isinstance(g, dict) else str(g) for g in raw_g_list if g]

        # Plot
        plots = data.get("plots", {}).get("edges", []) if isinstance(data.get("plots"), dict) else []
        overview = ""
        if plots and isinstance(plots[0], dict):
            overview = plots[0].get("node", {}).get("text", {}).get("plainText", "")
        elif isinstance(data.get("overview"), str):
            overview = data["overview"]

        # Credits
        credits_edges = data.get("credits", {}).get("edges", []) if isinstance(data.get("credits"), dict) else []
        cast: List[PersonDTO] = []
        crew: List[PersonDTO] = []

        for edge in credits_edges:
            node = edge.get("node", {})
            p_name = node.get("name", {}).get("nameText", {}).get("text", "")
            cat = str(node.get("category", {}).get("text", "")).lower()
            if not p_name:
                continue
            if "actor" in cat or "actress" in cat:
                cast.append(PersonDTO(name=p_name, role="actor", character_name=node.get("characters")))
            elif "director" in cat:
                crew.append(PersonDTO(name=p_name, role="director"))
            elif "writer" in cat:
                crew.append(PersonDTO(name=p_name, role="writer"))

        imdb_url = f"https://www.imdb.com/title/{imdb_id}/" if imdb_id else None

        provenance = {
            "title": "imdb",
            "release_date": "imdb",
            "runtime_seconds": "imdb",
            "imdb_rating": "imdb",
            "imdb_vote_count": "imdb",
            "genres": "imdb",
            "overview": "imdb",
            "cast": "imdb",
            "crew": "imdb",
            "imdb_url": "imdb",
        }

        from services.ingestion.dtos import IngestionState
        enrichment_state = IngestionState.CANONICAL_ENRICHED.value if (title and imdb_id) else IngestionState.CANONICAL_ENRICHMENT_PENDING.value

        return NormalizedContentDTO(
            external_ids={"imdb": imdb_id} if imdb_id else {},
            entity_type=entity_type,
            title=title,
            original_title=original_title,
            overview=overview,
            release_date=release_date,
            runtime=runtime_min,
            runtime_seconds=runtime_sec,
            genres=genres,
            average_rating=imdb_rating,
            vote_count=imdb_vote_count,
            imdb_rating=imdb_rating,
            imdb_vote_count=imdb_vote_count,
            imdb_url=imdb_url,
            cast=cast,
            crew=crew,
            source_connector="imdb",
            provenance=provenance,
            enrichment_state=enrichment_state,
        )

    def _normalize_tmdb(self, data: dict, entity_type: str) -> NormalizedContentDTO:
        """Normalize a TMDB API response into canonical format."""
        is_movie = entity_type == "movie"

        # Title
        title = data.get("title" if is_movie else "name", "Untitled")
        original_title = data.get("original_title" if is_movie else "original_name", title)

        # Release date
        release_date = data.get("release_date" if is_movie else "first_air_date", "")

        # Genres — TMDB returns [{"id": 28, "name": "Action"}, ...]
        raw_genres = data.get("genres", [])
        genres = self._extract_genre_names(raw_genres)

        # External IDs
        tmdb_id = str(data.get("id", ""))
        external_ids: Dict[str, str] = {"tmdb": tmdb_id}
        imdb_id = data.get("imdb_id")
        if imdb_id:
            external_ids["imdb"] = imdb_id

        # Images
        poster_url = self._build_image_url(data.get("poster_path"), "w500")
        backdrop_url = self._build_image_url(data.get("backdrop_path"), "w1280")

        # Credits
        credits = data.get("credits", {})
        cast = self._extract_cast(credits.get("cast", []))
        crew = self._extract_crew(credits.get("crew", []))

        # Runtime
        if is_movie:
            runtime = data.get("runtime")
        else:
            ep_runtimes = data.get("episode_run_time", [])
            runtime = ep_runtimes[0] if ep_runtimes else None

        # Series-specific
        total_seasons = data.get("number_of_seasons") if not is_movie else None
        total_episodes = data.get("number_of_episodes") if not is_movie else None
        in_production = data.get("in_production") if not is_movie else None

        # Seasons (for series)
        seasons: Optional[List[SeasonDTO]] = None
        if not is_movie and "seasons" in data:
            seasons = self._extract_seasons(data["seasons"])

        provenance = {
            "poster_url": "tmdb",
            "backdrop_url": "tmdb",
            "popularity": "tmdb",
        }
        from services.ingestion.dtos import IngestionState
        enrichment_state = IngestionState.CANONICAL_ENRICHMENT_PENDING.value if "imdb" not in external_ids else IngestionState.IDENTITY_RESOLVED.value

        return NormalizedContentDTO(
            external_ids=external_ids,
            entity_type=entity_type,
            title=title,
            original_title=original_title,
            overview=data.get("overview", ""),
            tagline=data.get("tagline"),
            release_date=release_date,
            runtime=runtime,
            runtime_seconds=(runtime * 60) if runtime else None,
            language=data.get("original_language", "en"),
            genres=genres,
            poster_url=poster_url,
            backdrop_url=backdrop_url,
            popularity=float(data.get("popularity", 0.0)),
            average_rating=float(data.get("vote_average", 0.0)),
            vote_count=int(data.get("vote_count", 0)),
            cast=cast,
            crew=crew,
            total_seasons=total_seasons,
            total_episodes=total_episodes,
            in_production=in_production,
            seasons=seasons,
            source_connector="tmdb",
            source_payload_hash="",
            provenance=provenance,
            enrichment_state=enrichment_state,
        )

    def _normalize_generic(self, data: dict, entity_type: str, connector: str) -> NormalizedContentDTO:
        """Fallback normalizer for unknown connector formats."""
        title = data.get("title") or data.get("name") or "Untitled"
        external_id = str(data.get("id") or data.get("external_id", ""))

        return NormalizedContentDTO(
            external_ids={connector: external_id},
            entity_type=entity_type,
            title=title,
            overview=data.get("overview", ""),
            language=data.get("language", "en"),
            popularity=float(data.get("popularity", 0.0)),
            average_rating=float(data.get("rating", 0.0)),
            source_connector=connector,
            source_payload_hash="",
        )

    # --- Helper Methods ---

    @staticmethod
    def _extract_genre_names(raw_genres) -> List[str]:
        if not raw_genres:
            return []
        if isinstance(raw_genres, list):
            return [
                g["name"] if isinstance(g, dict) else str(g)
                for g in raw_genres
                if g
            ]
        return [str(raw_genres)]

    @staticmethod
    def _build_image_url(path: Optional[str], size: str) -> Optional[str]:
        if not path:
            return None
        return f"{TMDB_IMAGE_BASE}{size}{path}"

    @staticmethod
    def _extract_cast(raw_cast: list, limit: int = 10) -> List[PersonDTO]:
        cast = []
        for i, c in enumerate(raw_cast[:limit]):
            cast.append(PersonDTO(
                name=c.get("name", ""),
                role="actor",
                character_name=c.get("character"),
                profile_url=f"{TMDB_IMAGE_BASE}w185{c['profile_path']}" if c.get("profile_path") else None,
                order=c.get("order", i),
            ))
        return cast

    @staticmethod
    def _extract_crew(raw_crew: list) -> List[PersonDTO]:
        """Extract directors, writers, and producers from TMDB crew list."""
        target_jobs = {"Director", "Writer", "Screenplay", "Executive Producer"}
        crew = []
        seen = set()
        for c in raw_crew:
            job = c.get("job", "")
            name = c.get("name", "")
            key = f"{name}:{job}"
            if job in target_jobs and key not in seen:
                seen.add(key)
                role_map = {
                    "Director": "director",
                    "Writer": "writer",
                    "Screenplay": "writer",
                    "Executive Producer": "producer",
                }
                crew.append(PersonDTO(
                    name=name,
                    role=role_map.get(job, "crew"),
                    profile_url=f"{TMDB_IMAGE_BASE}w185{c['profile_path']}" if c.get("profile_path") else None,
                    order=0,
                ))
        return crew

    @staticmethod
    def _extract_seasons(raw_seasons: list) -> List[SeasonDTO]:
        seasons = []
        for s in raw_seasons:
            season_num = s.get("season_number", 0)
            if season_num == 0:
                continue  # Skip "Specials" season
            seasons.append(SeasonDTO(
                season_number=season_num,
                title=s.get("name"),
                overview=s.get("overview"),
                poster_url=f"{TMDB_IMAGE_BASE}w500{s['poster_path']}" if s.get("poster_path") else None,
                air_date=s.get("air_date"),
                episode_count=s.get("episode_count", 0),
                episodes=[],  # Episodes are fetched separately if needed
            ))
        return seasons
