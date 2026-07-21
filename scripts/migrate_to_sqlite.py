import os
import sys
import csv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.repository.catalog_db import CatalogRepository

def migrate():
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/raw/movies.csv'))
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return
        
    repo = CatalogRepository()
    
    print(f"Migrating data from {csv_path} to SQLite...")
    
    success_count = 0
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                item_id = int(row.get('item_id', 0))
                tmdb_id = row.get('tmdb_id')
                if tmdb_id:
                    try:
                        tmdb_id = int(tmdb_id)
                    except:
                        tmdb_id = None
                
                movie_data = {
                    'item_id': item_id,
                    'tmdb_id': tmdb_id,
                    'title': row.get('title', ''),
                    'original_title': row.get('original_title', ''),
                    'release_date': row.get('release_date', ''),
                    'year': str(row.get('year', '')),
                    'runtime': str(row.get('runtime', '')),
                    'genres': row.get('genres', ''),
                    'overview': row.get('overview', ''),
                    'tagline': row.get('tagline', ''),
                    'director': row.get('director', ''),
                    'cast': row.get('cast', ''),
                    'poster_url': row.get('poster_url', ''),
                    'backdrop_url': row.get('backdrop_url', ''),
                    'rating': float(row.get('rating', 0.0) or 0.0),
                    'popularity': float(row.get('popularity', 0.0) or 0.0),
                    'language': row.get('language', ''),
                    'content_type': row.get('content_type', 'movie'),
                    'themes': row.get('themes', '')
                }
                repo.save(movie_data)
                success_count += 1
            except Exception as e:
                print(f"Error migrating row {row.get('item_id')}: {e}")
                
    print(f"Successfully migrated {success_count} movies to SQLite.")

if __name__ == "__main__":
    migrate()
