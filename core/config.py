from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache

class Settings(BaseSettings):
    # Base application settings
    app_name: str = "Streamora Production Platform"
    environment: str = Field(default="development", env="STREAMORA_ENV")
    
    # Feature Flags
    enable_ai_streaming: bool = Field(default=False, env="ENABLE_AI_STREAMING")
    enable_semantic_cache: bool = Field(default=False, env="ENABLE_SEMANTIC_CACHE")
    enable_experimental_recommender: bool = Field(default=False, env="ENABLE_EXPERIMENTAL_RECOMMENDER")
    enable_beta_homepage: bool = Field(default=False, env="ENABLE_BETA_HOMEPAGE")
    
    # Database Settings
    database_url: str = Field(default="sqlite:///data/streamora.db", env="DATABASE_URL")
    
    # Cache Settings
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Observability
    enable_telemetry: bool = Field(default=False, env="ENABLE_TELEMETRY")
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached instance of the settings object.
    Since it uses lru_cache, settings are loaded once from env vars / .env file
    at startup and reused across the application.
    """
    return Settings()
