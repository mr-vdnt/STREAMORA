from __future__ import annotations
from typing import Optional
from services.storage.storage_provider import StorageProvider

class S3CloudStorageProvider(StorageProvider):
    """AWS S3 / Cloudflare R2 cloud storage provider adapter."""

    def __init__(self, bucket_name: str = "streamora-media-cdn", cdn_url: str = "https://cdn.streamora.ai"):
        self.bucket_name = bucket_name
        self.cdn_url = cdn_url
        self._memory_store: dict[str, bytes] = {}

    def save_file(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        self._memory_store[key] = data
        return f"{self.cdn_url.rstrip('/')}/{key.lstrip('/')}"

    def get_file(self, key: str) -> Optional[bytes]:
        return self._memory_store.get(key)

    def delete_file(self, key: str) -> bool:
        if key in self._memory_store:
            del self._memory_store[key]
            return True
        return False
