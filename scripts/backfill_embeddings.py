import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.repository.catalog_db import CatalogRepository
from services.content_intelligence.embedding_engine import EmbeddingEngine

def backfill():
    repo = CatalogRepository()
    embedder = EmbeddingEngine()
    
    movies = repo.get_all()
    print(f"Loaded {len(movies)} movies from DB. Generating embeddings...")
    
    count = 0
    for iid, movie in movies.items():
        if iid in embedder.id_mapping:
            continue
            
        # Combine rich metadata for semantic representation
        text = f"{movie.get('title', '')} {movie.get('genres', '')} {movie.get('director', '')} {movie.get('overview', '')}"
        embedder.add_item(iid, text)
        count += 1
        
        if count % 10 == 0:
            print(f"Generated {count} embeddings...")
            
    print(f"Successfully generated and saved {count} new embeddings.")

if __name__ == "__main__":
    backfill()
