from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache
from typing import Optional, List

class AppSettings(BaseSettings):
    app_name: str = "Streamora Production Platform"
    environment: str = Field(default="development", validation_alias="STREAMORA_ENV")
    debug: bool = False
    api_prefix: str = "/api/v2"

class DatabaseSettings(BaseSettings):
    database_url: str = Field(default="sqlite:///data/catalog_v2.db", validation_alias="DATABASE_URL")
    pool_size: int = 20
    max_overflow: int = 10

class RedisSettings(BaseSettings):
    redis_url: str = Field(default="redis://localhost:6379", validation_alias="REDIS_URL")
    default_ttl: int = 300
    lock_timeout: int = 10

class TMDBSettings(BaseSettings):
    tmdb_api_key: Optional[str] = Field(default=None, validation_alias="TMDB_API_KEY")
    tmdb_base_url: str = "https://api.themoviedb.org/3"

class TelemetrySettings(BaseSettings):
    enable_telemetry: bool = Field(default=False, validation_alias="ENABLE_TELEMETRY")
    otlp_endpoint: str = "http://localhost:4317"

class SecuritySettings(BaseSettings):
    jwt_secret_key: str = Field(default="fallback_production_secret_key_change_me", validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:8000"]

class SearchSettings(BaseSettings):
    enable_semantic_search: bool = True
    max_search_results: int = 50

class RecommendationSettings(BaseSettings):
    enable_diversity_capping: bool = True
    max_items_per_genre: int = 3
    default_shelf_limit: int = 15

class Settings(BaseSettings):
    app: AppSettings = AppSettings()
    db: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    tmdb: TMDBSettings = TMDBSettings()
    telemetry: TelemetrySettings = TelemetrySettings()
    security: SecuritySettings = SecuritySettings()
    search: SearchSettings = SearchSettings()
    recommendation: RecommendationSettings = RecommendationSettings()

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

@lru_cache()
def get_settings() -> Settings:
    return Settings()
