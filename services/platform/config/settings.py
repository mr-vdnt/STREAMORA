import os
from typing import Dict, Any

class Settings:
    """Centralized configuration for the Streamora platform."""
    
    def __init__(self):
        # Environment
        self.ENV = os.environ.get("STREAMORA_ENV", "development")
        
        # Parallel Execution
        self.MAX_GENERATOR_WORKERS = int(os.environ.get("MAX_GENERATOR_WORKERS", "5"))
        
        # LLM Settings
        self.LLM_MODEL = os.environ.get("LLM_MODEL", "llama3")
        self.LLM_TIMEOUT_MS = int(os.environ.get("LLM_TIMEOUT_MS", "3000"))
        
        # Paths
        self.MOVIES_CSV_PATH = os.environ.get("MOVIES_CSV_PATH", "data/raw/movies.csv")
        self.FAISS_INDEX_PATH = os.environ.get("FAISS_INDEX_PATH", "data/index/movies.index")
        
        # Caching
        self.CACHE_DEFAULT_TTL = int(os.environ.get("CACHE_DEFAULT_TTL", "300"))
        
        # Weights for Scoring Engine (Default fallback)
        self.DEFAULT_WEIGHTS = {
            "retrieval_fusion_score": 25.0,
            "genre_overlap": 15.0,
            "theme_overlap": 15.0,
            "director_match": 10.0,
            "actor_match": 5.0,
            "popularity_boost": 5.0,
            "vote_average_boost": 5.0,
            "personalization_score": 5.0,
            "graph_similarity": 5.0,
            "shared_theme_score": 3.0,
            "shared_actor_score": 3.0,
            "shared_director_score": 4.0
        }

# Global singleton for settings
settings = Settings()
