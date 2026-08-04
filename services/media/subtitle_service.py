from __future__ import annotations
from typing import List, Dict, Any

class SubtitleService:
    """Subtitle track resolver for WebVTT multi-language streaming."""

    def get_subtitle_tracks(self, content_id: int) -> List[Dict[str, str]]:
        return [
            {"language": "English", "code": "en", "url": f"https://cdn.streamora.ai/subtitles/{content_id}/en.vtt", "is_default": True},
            {"language": "Spanish", "code": "es", "url": f"https://cdn.streamora.ai/subtitles/{content_id}/es.vtt", "is_default": False},
            {"language": "French", "code": "fr", "url": f"https://cdn.streamora.ai/subtitles/{content_id}/fr.vtt", "is_default": False},
            {"language": "German", "code": "de", "url": f"https://cdn.streamora.ai/subtitles/{content_id}/de.vtt", "is_default": False}
        ]
