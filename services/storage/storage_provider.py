from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional

class StorageProvider(ABC):
    """Abstract Base Class for binary asset storage providers (posters, trailers, subtitles)."""

    @abstractmethod
    def save_file(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Save binary data and return access URL."""
        ...

    @abstractmethod
    def get_file(self, key: str) -> Optional[bytes]:
        """Fetch binary data by key."""
        ...

    @abstractmethod
    def delete_file(self, key: str) -> bool:
        """Delete binary file by key."""
        ...
