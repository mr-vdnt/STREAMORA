from __future__ import annotations
from typing import Dict, Any, Optional
from services.media.stream_resolver import StreamResolver
from services.media.artwork_service import ArtworkService
from services.media.subtitle_service import SubtitleService

class MediaPlatformService:
    """Unified Media & CDN Platform facade combining stream signing, artwork CDN, and subtitle management."""

    def __init__(self):
        self.stream_resolver = StreamResolver()
        self.artwork_service = ArtworkService()
        self.subtitle_service = SubtitleService()

    @staticmethod
    def sanitize_metadata(meta: Dict[str, Any]) -> Dict[str, Any]:
        """Strip placeholder values ('Unknown Director', 'Undisclosed', 'Standalone', 'N/A') from DTOs."""
        placeholders = {"unknown director", "undisclosed", "standalone", "n/a", "unknown actor", "unknown", "none"}
        sanitized = {}
        for key, val in meta.items():
            if isinstance(val, str) and val.strip().lower() in placeholders:
                continue
            sanitized[key] = val
        return sanitized

    def get_full_media_bundle(self, content_id: int, backdrop_path: Optional[str] = None, poster_path: Optional[str] = None) -> Dict[str, Any]:
        manifest = self.stream_resolver.get_manifest_details(content_id)
        artworks = self.artwork_service.get_content_artwork_bundle(backdrop_path, poster_path)
        subtitles = self.subtitle_service.get_subtitle_tracks(content_id)

        return {
            "content_id": content_id,
            "manifest": manifest,
            "artwork": artworks,
            "subtitles": subtitles
        }
