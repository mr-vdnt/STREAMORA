from __future__ import annotations
from typing import Dict, Any, Optional

class ArtworkService:
    """CDN image URL resolver for posters, backdrops, hero graphics, and thumbnails."""

    BASE_CDN = "https://image.tmdb.org/t/p/"

    def format_artwork(self, path: Optional[str], size: str = "w500") -> str:
        if not path:
            return f"https://cdn.streamora.ai/assets/placeholder_{size}.png"
        if path.startswith("http"):
            return path
        clean_path = path.lstrip("/")
        return f"{self.BASE_CDN}{size}/{clean_path}"

    def get_content_artwork_bundle(self, backdrop_path: Optional[str], poster_path: Optional[str]) -> Dict[str, str]:
        return {
            "poster_small": self.format_artwork(poster_path, "w185"),
            "poster_medium": self.format_artwork(poster_path, "w500"),
            "poster_large": self.format_artwork(poster_path, "original"),
            "backdrop_medium": self.format_artwork(backdrop_path, "w780"),
            "backdrop_hero": self.format_artwork(backdrop_path, "w1280"),
            "backdrop_original": self.format_artwork(backdrop_path, "original"),
        }
