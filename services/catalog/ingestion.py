import os
import csv
import json
import requests
import faiss
from services.ranking.main import movies_db, faiss_index, faiss_id_mapping, model

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

def ingest_from_tmdb(query: str) -> dict | None:
    """
    Ingest a movie/series from TMDB if it is missing from the local catalog.
    Returns the ingested item_id, or None if not found.
    """
    if not TMDB_API_KEY:
        print("Warning: TMDB_API_KEY not set.")
        return None

    url = f"https://api.themoviedb.org/3/search/multi?query={query}&include_adult=false&language=en-US&page=1"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {TMDB_API_KEY}"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code != 200:
            return None
            
        results = resp.json().get("results", [])
        for item in results:
            if item.get("media_type") not in ["movie", "tv"]:
                continue
                
            tmdb_id = item.get("id")
            
            # Check if it already exists by TMDB ID
            for iid, row in movies_db.items():
                if str(row.get("tmdb_id", "")) == str(tmdb_id):
                    return iid
                    
            # Create a new positive internal ID
            new_id = max([k for k in movies_db.keys()] + [0]) + 1
            
            title = item.get("title") or item.get("name") or "Unknown Title"
            poster_path = item.get("poster_path")
            backdrop_path = item.get("backdrop_path")
            
            row = {
                "item_id": new_id,
                "tmdb_id": tmdb_id,
                "content_type": "movie" if item.get("media_type") == "movie" else "series",
                "title": title,
                "original_title": item.get("original_title") or item.get("original_name") or title,
                "release_date": item.get("release_date", item.get("first_air_date", "")),
                "year": item.get("release_date", item.get("first_air_date", ""))[:4],
                "overview": item.get("overview", ""),
                "poster_url": f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "",
                "backdrop_url": f"https://image.tmdb.org/t/p/w1280{backdrop_path}" if backdrop_path else "",
                "rating": item.get("vote_average", 7.0),
                "genres": "Unknown", # TMDB provides genre IDs, would need mapping for real genres
                "director": "Unknown",
                "cast": "Unknown"
            }
            
            # 1. Update in-memory DB
            movies_db[new_id] = row
            
            # 2. Append to movies.csv (ephemeral on Render, but works per-session)
            if os.path.exists("data/raw/movies.csv"):
                with open("data/raw/movies.csv", "a", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=row.keys())
                    writer.writerow(row)
                    
            # 3. Generate and append FAISS embedding
            if model is not None and faiss_index is not None:
                text = f"{row['title']} {row['genres']} {row['overview']}"
                embedding = model.encode([text])[0].reshape(1, -1)
                faiss_index.add(embedding)
                faiss_id_mapping.append(new_id)
                
                if os.path.exists("data/index/semantic_items_mapping.json"):
                    with open("data/index/semantic_items_mapping.json", "w") as f:
                        json.dump(faiss_id_mapping, f)
            
            return new_id
            
        return None
    except Exception as e:
        print(f"Ingestion Failed: {e}")
        return None
