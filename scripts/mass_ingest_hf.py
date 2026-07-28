import os
import sys
import pandas as pd
from datasets import load_dataset
from datetime import datetime
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.repository.catalog_db import CatalogRepository, Movie, TVSeries, Content

def generate_slug(title, year):
    import re
    clean_title = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    return f"{clean_title}-{year}"

def build_mass_catalog():
    repo = CatalogRepository()
    
    print("Loading Movies dataset (Pablinho/movies-dataset)...")
    ds = load_dataset('Pablinho/movies-dataset', split='train')
    df = ds.to_pandas()
    
    unique_items = []
    seen_ids = set()
    seen_slugs = set()
    
    df['Popularity'] = pd.to_numeric(df['Popularity'], errors='coerce').fillna(0)
    df = df.sort_values(by='Popularity', ascending=False)
    
    movies_to_insert = []
    series_to_insert = []
    
    item_id_counter = 1
    
    # Load real TV Shows (We will manually inject 5 highly popular series to ensure strict separation)
    real_series = [
        {
            "tmdb_id": 1399, "title": "Game of Thrones", "year": "2011",
            "poster_url": "https://image.tmdb.org/t/p/w500/1XS1oqL89opfnbLl8WnZY1O1uJx.jpg",
            "genres": "Sci-Fi & Fantasy|Drama|Action & Adventure", "language": "en"
        },
        {
            "tmdb_id": 66732, "title": "Stranger Things", "year": "2016",
            "poster_url": "https://image.tmdb.org/t/p/w500/49WJfeN0moxb9IPfGn8Slgw5LOM.jpg",
            "genres": "Drama|Sci-Fi & Fantasy|Mystery", "language": "en"
        },
        {
            "tmdb_id": 1396, "title": "Breaking Bad", "year": "2008",
            "poster_url": "https://image.tmdb.org/t/p/w500/ggFHVNu6YYI5L9pCfOacjizRGt.jpg",
            "genres": "Drama|Crime", "language": "en"
        },
        {
            "tmdb_id": 93405, "title": "Squid Game", "year": "2021",
            "poster_url": "https://image.tmdb.org/t/p/w500/dDlEmu3EZ0Pgg93K2SVNLCjCSvE.jpg",
            "genres": "Action & Adventure|Mystery|Drama", "language": "ko"
        },
        {
            "tmdb_id": 31911, "title": "Fullmetal Alchemist: Brotherhood", "year": "2009",
            "poster_url": "https://image.tmdb.org/t/p/w500/5ZFVN90pZleP50c8h4PBN5uV4aE.jpg",
            "genres": "Action & Adventure|Animation|Sci-Fi & Fantasy", "language": "ja", "themes": "anime"
        }
    ]

    real_series_titles = {s['title'].lower() for s in real_series}

    for _, row in df.head(10000).iterrows():
        title = str(row.get('Title', 'Unknown'))
        if title.lower() in real_series_titles:
            continue
            
        tmdb_id = int(row.get('id', item_id_counter * 1000) if pd.notna(row.get('id')) else item_id_counter * 1000)
        
        if tmdb_id in seen_ids:
            continue
            
        poster_url = str(row.get('Poster_Url', ''))
        if not poster_url or 'http' not in poster_url:
            continue
            
        title = str(row.get('Title', 'Unknown'))
        year = str(row.get('Release_Date', ''))[:4] if pd.notna(row.get('Release_Date')) else "Unknown"
        slug = generate_slug(title, year)
        
        if slug in seen_slugs:
            slug = f"{slug}-{item_id_counter}"
            
        seen_ids.add(tmdb_id)
        seen_slugs.add(slug)
        
        genres = str(row.get('Genre', 'Drama')).replace(', ', '|')
        lang = str(row.get('Original_Language', 'en')).lower()
        rating = float(row.get('Vote_Average', 0.0))
        popularity = float(row.get('Popularity', 0.0))
        
        themes = ""
        if lang in ['hi']: themes += "|bollywood"
        if lang in ['te', 'ta', 'ml', 'kn']: themes += "|south_indian"
        if lang == 'ko': themes += "|korean"
        if lang == 'ja' and 'Animation' in genres: themes += "|anime"
        if rating > 8.0 and popularity > 50: themes += "|oscars|classics"
            
        movies_to_insert.append({
            "tmdb_id": tmdb_id,
            "slug": slug,
            "entity_type": "movie",
            "title": title,
            "original_title": title,
            "release_date": str(row.get('Release_Date', '')),
            "year": year,
            "genres": genres,
            "overview": str(row.get('Overview', '')),
            "poster_url": poster_url,
            "backdrop_url": poster_url,
            "rating": rating,
            "popularity": popularity,
            "language": lang,
            "themes": themes.strip('|'),
            "runtime": 120
        })
        item_id_counter += 1

    # Removed real_series definition from here since it was moved up

    for s in real_series:
        slug = generate_slug(s['title'], s['year'])
        if slug in seen_slugs:
            slug = f"{slug}-tv"
        seen_slugs.add(slug)
        seen_ids.add(s['tmdb_id'])
        
        series_to_insert.append({
            "tmdb_id": s['tmdb_id'],
            "slug": slug,
            "entity_type": "tvseries",
            "title": s['title'],
            "year": s['year'],
            "poster_url": s['poster_url'],
            "backdrop_url": s['poster_url'],
            "genres": s['genres'],
            "language": s['language'],
            "themes": s.get('themes', ''),
            "popularity": 90.0,
            "rating": 8.5,
            "total_seasons": 5,
            "total_episodes": 50
        })

    # Bulk insert
    with repo.get_session() as session:
        print("Recreating database schema...")
        from services.repository.catalog_db import Base
        Base.metadata.drop_all(repo.engine)
        Base.metadata.create_all(repo.engine)
        
        chunk_size = 1000
        for i in range(0, len(movies_to_insert), chunk_size):
            chunk = movies_to_insert[i:i+chunk_size]
            objects = [Movie(**item) for item in chunk]
            session.add_all(objects)
            session.commit()
            print(f"Inserted {i + len(chunk)} / {len(movies_to_insert)} movies")

        # Cleanup collisions is handled before insertion now.
        
        objects = [TVSeries(**item) for item in series_to_insert]
        session.add_all(objects)
        session.commit()
        print(f"Inserted {len(series_to_insert)} real TV series")

    print("Database population complete. Ready for RC2.25 validation.")

if __name__ == "__main__":
    build_mass_catalog()
