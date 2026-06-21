import requests
import pandas as pd
import json
import time

API_KEY = "78a8e3ba2f60ffc8e3a9194370a4fb79"
BASE_URL = "https://api.themoviedb.org/3"

# We will map genre IDs to names manually or fetch them
def get_genre_map():
    try:
        res_m = requests.get(f"{BASE_URL}/genre/movie/list?api_key={API_KEY}").json()
        res_t = requests.get(f"{BASE_URL}/genre/tv/list?api_key={API_KEY}").json()
        gmap = {}
        for g in res_m.get('genres', []): gmap[g['id']] = g['name']
        for g in res_t.get('genres', []): gmap[g['id']] = g['name']
        return gmap
    except:
        return {}

genre_map = get_genre_map()

queries = [
    # Hollywood Blockbusters
    {"endpoint": "/discover/movie", "params": {"with_original_language": "en", "sort_by": "popularity.desc"}},
    # Trending TV Series
    {"endpoint": "/discover/tv", "params": {"with_original_language": "en", "sort_by": "popularity.desc"}},
    # Bollywood
    {"endpoint": "/discover/movie", "params": {"with_original_language": "hi", "sort_by": "popularity.desc"}},
    # K-Dramas
    {"endpoint": "/discover/tv", "params": {"with_original_language": "ko", "sort_by": "popularity.desc"}},
    # Anime
    {"endpoint": "/discover/tv", "params": {"with_original_language": "ja", "with_genres": "16", "sort_by": "popularity.desc"}},
    # Kollywood / Tollywood
    {"endpoint": "/discover/movie", "params": {"with_original_language": "te", "sort_by": "popularity.desc"}},
    {"endpoint": "/discover/movie", "params": {"with_original_language": "ta", "sort_by": "popularity.desc"}},
    # Spanish
    {"endpoint": "/discover/tv", "params": {"with_original_language": "es", "sort_by": "popularity.desc"}},
]

all_items = []
item_id_counter = 1

print("Fetching TMDB Data...")
for q in queries:
    # Fetch 2 pages per category to get a solid dataset (40 items each)
    for page in range(1, 3):
        url = f"{BASE_URL}{q['endpoint']}?api_key={API_KEY}&page={page}"
        for k, v in q['params'].items():
            url += f"&{k}={v}"
        
        try:
            resp = requests.get(url).json()
            results = resp.get('results', [])
            for res in results:
                title = res.get('title') or res.get('name')
                if not title: continue
                
                year = ""
                release_date = res.get('release_date') or res.get('first_air_date')
                if release_date:
                    year = release_date.split('-')[0]
                    
                genre_names = [genre_map.get(gid, "Unknown") for gid in res.get('genre_ids', [])]
                
                poster_path = res.get('poster_path')
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""
                
                backdrop_path = res.get('backdrop_path')
                backdrop_url = f"https://image.tmdb.org/t/p/w1280{backdrop_path}" if backdrop_path else ""
                
                all_items.append({
                    "item_id": item_id_counter,
                    "tmdb_id": res.get('id'),
                    "title": f"{title} ({year})" if year else title,
                    "original_title": title,
                    "overview": res.get('overview', '').replace('\n', ' '),
                    "rating": res.get('vote_average', 0.0),
                    "popularity": res.get('popularity', 0.0),
                    "language": res.get('original_language', ''),
                    "genres": "|".join(genre_names),
                    "poster_url": poster_url,
                    "backdrop_url": backdrop_url,
                    "is_adult": res.get('adult', False)
                })
                item_id_counter += 1
        except Exception as e:
            print("Error fetching:", e)
        time.sleep(0.1) # rate limit prevention

df = pd.DataFrame(all_items)
df.drop_duplicates(subset=['tmdb_id'], inplace=True)

# Re-assign sequential item_ids after deduplication to ensure contiguous
df['item_id'] = range(1, len(df) + 1)

df.to_csv("data/raw/movies.csv", index=False)
print(f"Successfully saved {len(df)} items to data/raw/movies.csv!")
