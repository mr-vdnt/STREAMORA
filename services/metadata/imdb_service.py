import os

class ConfigurationError(Exception):
    pass

class IMDbMetadataService:
    def __init__(self):
        self.enabled = os.environ.get("IMDB_API_ENABLED", "false").lower() == "true"
        self.api_key = os.environ.get("IMDB_API_KEY")
        if self.enabled and not self.api_key:
            raise ConfigurationError("IMDB_API_KEY must be set when IMDB_API_ENABLED is true.")

    def is_available(self) -> bool:
        return self.enabled

    def get_title_metadata(self, imdb_id: str) -> dict | None:
        if not self.is_available():
            return None
        return None

    def extract_imdb_id(self, external_identifiers: dict) -> str | None:
        """
        Check if external_identifiers table/dict has IMDb IDs and extract them.
        """
        if not external_identifiers:
            return None
        imdb_id = external_identifiers.get("imdb_id")
        if imdb_id and str(imdb_id).startswith("tt"):
            return imdb_id
        return None
