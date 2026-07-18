import os

def _bool_env(key: str, default: bool = True) -> bool:
    val = os.environ.get(key)
    if val is None:
        return default
    return str(val).lower() in ("1", "true", "yes", "on")

class RetrievalFlags:
    ENABLE_EXACT = _bool_env("ENABLE_EXACT", True)
    ENABLE_SEMANTIC = _bool_env("ENABLE_SEMANTIC", True)
    ENABLE_METADATA = _bool_env("ENABLE_METADATA", True)
    ENABLE_PERSONALIZATION = _bool_env("ENABLE_PERSONALIZATION", True)
    ENABLE_GRAPH = _bool_env("ENABLE_GRAPH", True)

class RankingFlags:
    ENABLE_BUSINESS_RULES = _bool_env("ENABLE_BUSINESS_RULES", True)
    ENABLE_DIVERSITY = _bool_env("ENABLE_DIVERSITY", True)

class PresentationFlags:
    ENABLE_LLM = _bool_env("ENABLE_LLM", True)

class PlatformFlags:
    ENABLE_CACHE = _bool_env("ENABLE_CACHE", True)
    ENABLE_TRACING = _bool_env("ENABLE_TRACING", True)
