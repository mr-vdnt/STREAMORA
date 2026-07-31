import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.repository.catalog_db import CatalogRepository, Content, Movie, TVSeries

def verify_catalog():
    repo = CatalogRepository()
    session = repo.get_session()
    
    print("Running Catalog Validation (RC2.25)...")
    errors = []
    
    # Check 1: Duplicate TMDB IDs == 0
    all_content = session.query(Content).all()
    tmdb_ids = [c.tmdb_id for c in all_content if c.tmdb_id is not None]
    duplicates = set([x for x in tmdb_ids if tmdb_ids.count(x) > 1])
    if duplicates:
        errors.append(f"Duplicate TMDB IDs found: {duplicates}")
        
    # Check 2: Movie-Series collisions == 0 (Titles)
    # Even if they have different TMDB IDs, we shouldn't have exact title collisions between Movie and TVSeries
    movie_titles = {c.title for c in all_content if c.entity_type == 'movie'}
    tv_titles = {c.title for c in all_content if c.entity_type == 'tvseries'}
    collisions = movie_titles.intersection(tv_titles)
    if collisions:
        errors.append(f"Movie-Series Title Collisions found: {collisions}")

    # Check 3: Entity Type Strictness
    movies = session.query(Movie).all()
    series = session.query(TVSeries).all()
    
    for m in movies:
        if m.entity_type != 'movie':
            errors.append(f"Invalid entity type for Movie ID {m.id}: {m.entity_type}")
            
    for s in series:
        if s.entity_type != 'tvseries':
            errors.append(f"Invalid entity type for TVSeries ID {s.id}: {s.entity_type}")
            
    # Check 4: Broken posters == 0
    missing_posters = [c.id for c in all_content if not c.poster_url or 'http' not in c.poster_url]
    if missing_posters:
        errors.append(f"Broken/missing posters found for {len(missing_posters)} items.")
        
    # Check 5: Basic Counts
    if len(movies) == 0:
        errors.append("0 Movies found in catalog.")
    if len(series) == 0:
        errors.append("0 TV Series found in catalog.")
        
    print(f"Total Content Items: {len(all_content)}")
    print(f"Total Movies: {len(movies)}")
    print(f"Total TV Series: {len(series)}")
    
    if errors:
        print("\n[FAILED] VALIDATION FAILED")
        for e in errors:
            try:
                print(f"  - {e}")
            except Exception as ex:
                print(f"  - Error printing message: {ex}")
        sys.exit(1)
    else:
        print("\n[PASSED] VALIDATION PASSED")
        sys.exit(0)

if __name__ == "__main__":
    verify_catalog()
