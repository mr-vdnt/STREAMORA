import os
from services.repository.catalog_db import CatalogRepository
from services.discovery.tmdb_resolver import TMDBResolver
from services.content_intelligence.embedding_engine import EmbeddingEngine

def ingest_from_tmdb(query: str) -> int | None:
    """
    Ingest a movie/series from TMDB if it is missing from the local catalog.
    Returns the ingested item_id, or None if not found.
    """
    resolver = TMDBResolver()
    repo = CatalogRepository()
    embedder = EmbeddingEngine()
    
    # 1. Search TMDB
    metadata = resolver.search_multi(query)
    if not metadata:
        return None
        
    tmdb_id = metadata.get("tmdb_id")
    
    # 2. Check if already exists in DB
    existing = repo.get_all()
    for iid, row in existing.items():
        if str(row.get("tmdb_id", "")) == str(tmdb_id):
            return iid
            
    # 3. Add to SQLite DB
    new_id = repo.add_item(metadata)
    
    # 4. Add to FAISS Vector Index
    text = f"{metadata.get('title', '')} {metadata.get('genres', '')} {metadata.get('director', '')} {metadata.get('overview', '')}"
    embedder.add_item(new_id, text)
    
    return new_id

