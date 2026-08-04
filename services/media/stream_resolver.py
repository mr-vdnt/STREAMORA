from __future__ import annotations
import hmac
import hashlib
import time
from typing import Dict, Any, List

class StreamResolver:
    """HLS stream manifest resolver and secure CDN token signer."""

    def __init__(self, cdn_secret: str = "streamora_cdn_secret_key_2026"):
        self.cdn_secret = cdn_secret

    def generate_signed_stream_url(self, content_id: int, quality: str = "1080p", ttl_seconds: int = 3600) -> str:
        expires_at = int(time.time()) + ttl_seconds
        payload = f"{content_id}:{quality}:{expires_at}"
        signature = hmac.new(self.cdn_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return f"https://cdn.streamora.ai/streams/{content_id}/{quality}/master.m3u8?expires={expires_at}&sig={signature}"

    def get_manifest_details(self, content_id: int) -> Dict[str, Any]:
        return {
            "content_id": content_id,
            "master_manifest_url": self.generate_signed_stream_url(content_id, "master"),
            "variants": [
                {"quality": "4K", "resolution": "3840x2160", "bitrate_kbps": 15000, "url": self.generate_signed_stream_url(content_id, "4k")},
                {"quality": "1080p", "resolution": "1920x1080", "bitrate_kbps": 6000, "url": self.generate_signed_stream_url(content_id, "1080p")},
                {"quality": "720p", "resolution": "1280x720", "bitrate_kbps": 3000, "url": self.generate_signed_stream_url(content_id, "720p")}
            ]
        }
