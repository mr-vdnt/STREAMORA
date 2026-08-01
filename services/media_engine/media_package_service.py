"""
STREAMORA - AMP Lite Media Package Service
Generates thin, provider-agnostic Media Package JSON payloads for frontend views.
"""
from typing import Dict, Any, Optional
from services.repository.movie_repository import MovieRepository
from services.repository.series_repository import SeriesRepository

class MediaPackageService:
    def __init__(self):
        self.movie_repo = MovieRepository()
        self.series_repo = SeriesRepository()

    def get_media_package(self, content_id: int, content_type: str = "movie") -> Dict[str, Any]:
        # 1. Lookup item
        item = None
        if content_type.lower() in ("movie", "movies"):
            item = self.movie_repo.get_by_id(content_id)
        else:
            item = self.series_repo.get_by_id(content_id)

        if not item:
            # Fallback to search across both
            item = self.movie_repo.get_by_id(content_id) or self.series_repo.get_by_id(content_id)

        # 2. Default YouTube Video ID (Inception / Standard Fallback)
        video_id = "JfVOs4VSpmA"
        if item:
            # If item has custom video_id stored, use it
            if item.get("video_id"):
                video_id = item.get("video_id")

        poster_url = item.get("poster_url", "") if item else ""
        backdrop_url = item.get("backdrop_url", "") if item else ""
        title = item.get("title", "Streamora Media") if item else "Streamora Media"

        # 3. Construct provider-agnostic Media Package
        return {
            "content_id": content_id,
            "title": title,
            "poster": {
                "url": poster_url if poster_url else "https://image.tmdb.org/t/p/w780/8Y41Oi0qwB7PlzToFi14SSvM3fB.jpg"
            },
            "backdrop": {
                "url": backdrop_url if backdrop_url else "https://image.tmdb.org/t/p/w1280/s3TBrRGB1iav7ySaV0StzOPLcfv.jpg",
                "is_dark": True
            },
            "logo": {
                "url": "/assets/logos/streamora_logo.svg"
            },
            "primary_video": {
                "player_type": "embed_iframe",
                "player_payload": {
                    "src": f"https://www.youtube.com/embed/{video_id}?autoplay=1&enablejsapi=1&rel=0&modestbranding=1",
                    "video_id": video_id,
                    "aspect_ratio": "16:9",
                    "allow_fullscreen": True
                },
                "fallback": {
                    "type": "external_url",
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "label": "Watch Official Trailer on YouTube"
                }
            },
            "providers": [
                {"name": "Netflix", "badge": "N", "color": "#E50914"},
                {"name": "Prime Video", "badge": "PRIME", "color": "#00A8E1"},
                {"name": "Disney+", "badge": "DISNEY+", "color": "#113CCF"}
            ]
        }
