import os
import requests

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

def fetch_live_tmdb_fallback(query: str, limit: int = 5) -> list[dict]:
    """
    Performs a live search against TMDB for queries that yield no local results.
    Transforms TMDB results into the internal Streamora schema.
    """
    if not TMDB_API_KEY:
        print("Warning: TMDB_API_KEY not set.")
        return []

    url = f"https://api.themoviedb.org/3/search/multi?query={query}&include_adult=false&language=en-US&page=1"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {TMDB_API_KEY}"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code != 200:
            return []
        
        results = resp.json().get("results", [])
        formatted_results = []
        
        for item in results:
            if item.get("media_type") not in ["movie", "tv"]:
                continue
                
            # Internal ID fallback logic (use negative IDs for external TMDB items to prevent conflicts)
            iid = -int(item.get("id", 0))
            
            title = item.get("title") or item.get("name") or "Unknown Title"
            poster_path = item.get("poster_path")
            backdrop_path = item.get("backdrop_path")
            
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""
            backdrop_url = f"https://image.tmdb.org/t/p/w1280{backdrop_path}" if backdrop_path else ""
            
            rich_meta = {
                "director": "TMDB Live Result",
                "cast": "",
                "year": item.get("release_date", item.get("first_air_date", ""))[:4],
                "rating": str(item.get("vote_average", "N/A")),
                "duration": "N/A",
                "genres": "Unknown",
                "why_recommended": "Live fetched from TMDB."
            }
            
            formatted_results.append({
                "item_id": iid,
                "title": title,
                "poster_url": poster_url,
                "backdrop_url": backdrop_url,
                "overview": item.get("overview", ""),
                "rich_metadata": rich_meta,
                "explanation": "Live fetched from TMDB."
            })
            
            if len(formatted_results) >= limit:
                break
                
        return formatted_results
    except Exception as e:
        print(f"TMDB Live Fetch Failed: {e}")
        return []
