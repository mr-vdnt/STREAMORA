from __future__ import annotations
import os
from typing import Optional
from services.storage.storage_provider import StorageProvider

class LocalStorageProvider(StorageProvider):
    """Local filesystem implementation of StorageProvider."""

    def __init__(self, base_dir: str = "./storage_data", base_url: str = "https://cdn.streamora.ai/local/"):
        self.base_dir = os.path.abspath(base_dir)
        self.base_url = base_url
        os.makedirs(self.base_dir, exist_ok=True)

    def save_file(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        file_path = os.path.join(self.base_dir, key)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(data)
        return f"{self.base_url.rstrip('/')}/{key.lstrip('/')}"

    def get_file(self, key: str) -> Optional[bytes]:
        file_path = os.path.join(self.base_dir, key)
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                return f.read()
        return None

    def delete_file(self, key: str) -> bool:
        file_path = os.path.join(self.base_dir, key)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
