import asyncio
import aiohttp
import os
import sys
from datetime import datetime

# Add root to sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.repository.catalog_db import CatalogRepository

API_KEY = "78a8e3ba2f60ffc8e3a9194370a4fb79"
BASE_URL = "https://api.tmdb.org/3"

# TMDB Genre Mapping
GENRE_MAP = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime", 
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History", 
    27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Science Fiction", 
    10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western",
    10759: "Action & Adventure", 10762: "Kids", 10763: "News", 10764: "Reality", 
    10765: "Sci-Fi & Fantasy", 10766: "Soap", 10767: "Talk", 10768: "War & Politics"
}

def get_genres(genre_ids):
    return "|".join([GENRE_MAP.get(gid, "") for gid in genre_ids if gid in GENRE_MAP])

async def fetch_page(session, url, params, page):
    p = params.copy()
    p["page"] = page
    p["api_key"] = API_KEY
    async with session.get(url, params=p) as response:
        if response.status == 200:
            return await response.json()
        return {"results": []}

async def fetch_category(session, endpoint, params, max_pages, label):
    print(f"Fetching {label}...")
    tasks = []
    for page in range(1, max_pages + 1):
        tasks.append(fetch_page(session, f"{BASE_URL}{endpoint}", params, page))
    
    results = await asyncio.gather(*tasks)
    items = []
    for res in results:
        items.extend(res.get("results", []))
    print(f"Fetched {len(items)} items for {label}")
    return items

async def main():
    repo = CatalogRepository()
    
    async with aiohttp.ClientSession() as session:
        # Define categories to fetch to reach ~15k total
        # 1. Global Popular Movies (200 pages = 4000)
        # 2. Global Popular TV (150 pages = 3000)
        # 3. Bollywood Movies (100 pages = 2000)
        # 4. South Indian Movies (100 pages = 2000)
        # 5. Anime TV (100 pages = 2000)
        # 6. Korean Dramas (100 pages = 2000)
        # 7. Documentaries (50 pages = 1000)
        # 8. Kids (50 pages = 1000)
        # 9. Classic Movies (50 pages = 1000)
        
        categories = [
            ("/discover/movie", {"sort_by": "popularity.desc"}, 200, "Global Movies"),
            ("/discover/tv", {"sort_by": "popularity.desc"}, 150, "Global TV"),
            ("/discover/movie", {"with_original_language": "hi", "sort_by": "popularity.desc"}, 100, "Bollywood"),
            ("/discover/movie", {"with_original_language": "te|ta|ml|kn", "sort_by": "popularity.desc"}, 100, "South Indian"),
            ("/discover/tv", {"with_original_language": "ja", "with_genres": "16", "sort_by": "popularity.desc"}, 100, "Anime"),
            ("/discover/tv", {"with_original_language": "ko", "sort_by": "popularity.desc"}, 100, "Korean Dramas"),
            ("/discover/movie", {"with_genres": "99", "sort_by": "popularity.desc"}, 50, "Documentaries"),
            ("/discover/movie", {"with_genres": "10751", "sort_by": "popularity.desc"}, 50, "Family/Kids"),
            ("/discover/movie", {"release_date.lte": "1995-01-01", "sort_by": "vote_average.desc", "vote_count.gte": 500}, 50, "Classics"),
            ("/discover/movie", {"with_watch_providers": "8", "watch_region": "US", "sort_by": "popularity.desc"}, 50, "Netflix"),
            ("/discover/movie", {"with_watch_providers": "9|119", "watch_region": "US", "sort_by": "popularity.desc"}, 50, "Prime"),
            ("/discover/movie", {"with_watch_providers": "337", "watch_region": "US", "sort_by": "popularity.desc"}, 50, "Disney"),
            ("/discover/movie", {"vote_average.gte": 8.0, "vote_count.gte": 2000, "sort_by": "popularity.desc"}, 50, "Oscars"),
        ]
        
        all_items = []
        for endpoint, params, max_pages, label in categories:
            items = await fetch_category(session, endpoint, params, max_pages, label)
            for item in items:
                item["_source_endpoint"] = endpoint
                item["_source_label"] = label
            all_items.extend(items)
            
    # Process and deduplicate
    print(f"Total items fetched before deduplication: {len(all_items)}")
    seen = set()
    unique_items = []
    
    for item in all_items:
        tmdb_id = item.get("id")
        if not tmdb_id or tmdb_id in seen:
            continue
            
        # Skip if no poster (rule: No broken posters)
        if not item.get("poster_path"):
            continue
            
        seen.add(tmdb_id)
        
        is_tv = "name" in item
        title = item.get("title") if not is_tv else item.get("name")
        orig_title = item.get("original_title") if not is_tv else item.get("original_name")
        date_str = item.get("release_date") if not is_tv else item.get("first_air_date")
        year = date_str[:4] if date_str and len(date_str) >= 4 else "Unknown"
        
        # Determine content_type
        content_type = "movie"
        if item["_source_label"] == "Anime":
            content_type = "anime"
        elif item["_source_label"] == "Documentaries":
            content_type = "documentary"
        elif is_tv:
            content_type = "series"
            
        genres = get_genres(item.get("genre_ids", []))
        if not genres:
            genres = "Drama"
            
        # Construct fallback images if backdrop is missing
        poster_url = f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}"
        backdrop_path = item.get("backdrop_path") or item.get("poster_path")
        backdrop_url = f"https://image.tmdb.org/t/p/w1280{backdrop_path}"
        
        themes = ""
        label = item.get("_source_label", "")
        if label in ["Netflix", "Prime", "Disney", "Oscars", "Classics"]:
            themes = label
        
        movie_data = {
            "tmdb_id": tmdb_id,
            "title": f"{title} ({year})" if year != "Unknown" else title,
            "original_title": orig_title,
            "release_date": date_str or "",
            "year": year,
            "runtime": "120 min" if not is_tv else "Multiple Seasons",
            "genres": genres,
            "overview": item.get("overview") or "",
            "poster_url": poster_url,
            "backdrop_url": backdrop_url,
            "rating": round(float(item.get("vote_average", 0)), 1),
            "popularity": round(float(item.get("popularity", 0)), 1),
            "language": item.get("original_language", "en"),
            "content_type": content_type,
            "themes": themes
        }
        
        unique_items.append(movie_data)
        
    print(f"Total unique items to insert: {len(unique_items)}")
    
    # Bulk insert
    with repo.get_session() as session:
        # Clear existing to ensure clean state
        from services.repository.catalog_db import MovieModel
        session.query(MovieModel).delete()
        
        # Insert in chunks
        chunk_size = 1000
        for i in range(0, len(unique_items), chunk_size):
            chunk = unique_items[i:i+chunk_size]
            objects = [MovieModel(item_id=j+1+i, **item) for j, item in enumerate(chunk)]
            session.bulk_save_objects(objects)
            session.commit()
            print(f"Inserted chunk {i//chunk_size + 1}")

    print("Database population complete.")

if __name__ == "__main__":
    asyncio.run(main())
