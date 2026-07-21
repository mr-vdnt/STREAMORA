import os
import requests
from typing import Dict, Any, Optional

class TMDBResolver:
    """
    Resolves missing titles via TMDB, enriching the catalog.
    """
    def __init__(self):
        self.api_key = os.getenv("TMDB_API_KEY")
        self.base_url = "https://api.themoviedb.org/3"
        self.image_base = "https://image.tmdb.org/t/p/"

    def search_multi(self, query: str) -> Optional[Dict[str, Any]]:
        """Search TMDB for a movie or TV show"""
        if not self.api_key:
            print("TMDB_API_KEY not set")
            return None
            
        url = f"{self.base_url}/search/multi"
        params = {
            "api_key": self.api_key,
            "query": query,
            "language": "en-US",
            "page": 1,
            "include_adult": "false"
        }
        try:
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            # Find first movie or tv result
            for result in data.get("results", []):
                media_type = result.get("media_type")
                if media_type in ["movie", "tv"]:
                    return self._fetch_details(result.get("id"), media_type)
            return None
        except Exception as e:
            print(f"Error searching TMDB for {query}: {e}")
            return None

    def _fetch_details(self, tmdb_id: int, media_type: str) -> Optional[Dict[str, Any]]:
        """Fetch full details and cast for a specific ID"""
        url = f"{self.base_url}/{media_type}/{tmdb_id}"
        params = {
            "api_key": self.api_key,
            "language": "en-US",
            "append_to_response": "credits,videos"
        }
        
        try:
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            return self._normalize_data(data, media_type)
        except Exception as e:
            print(f"Error fetching TMDB details for {tmdb_id}: {e}")
            return None

    def _normalize_data(self, data: dict, media_type: str) -> dict:
        """Convert TMDB payload into Streamora MovieRepository format"""
        is_movie = (media_type == "movie")
        
        title = data.get("title" if is_movie else "name", "")
        original_title = data.get("original_title" if is_movie else "original_name", "")
        release_date = data.get("release_date" if is_movie else "first_air_date", "")
        year = release_date.split("-")[0] if release_date else ""
        
        # Runtime calculation
        if is_movie:
            runtime = f"{data.get('runtime', 0)} min"
        else:
            ep_run = data.get("episode_run_time", [])
            runtime = f"{ep_run[0]} min" if ep_run else "Unknown"
            
        genres = "|".join([g.get("name", "") for g in data.get("genres", [])])
        
        # Extract Cast & Director
        credits = data.get("credits", {})
        cast = "|".join([c.get("name", "") for c in credits.get("cast", [])[:5]])
        
        director = ""
        for crew in credits.get("crew", []):
            if crew.get("job") == "Director" or crew.get("job") == "Executive Producer":
                director = crew.get("name", "")
                break
                
        poster_path = data.get("poster_path")
        backdrop_path = data.get("backdrop_path")
        
        poster_url = f"{self.image_base}w500{poster_path}" if poster_path else ""
        backdrop_url = f"{self.image_base}w1280{backdrop_path}" if backdrop_path else ""
        
        return {
            "tmdb_id": data.get("id"),
            "title": title,
            "original_title": original_title,
            "release_date": release_date,
            "year": year,
            "runtime": runtime,
            "genres": genres,
            "overview": data.get("overview", ""),
            "tagline": data.get("tagline", ""),
            "director": director,
            "cast": cast,
            "poster_url": poster_url,
            "backdrop_url": backdrop_url,
            "rating": data.get("vote_average", 0.0),
            "popularity": data.get("popularity", 0.0),
            "language": data.get("original_language", ""),
            "content_type": "movie" if is_movie else "series",
            "themes": "" # Will be populated by AI later if needed
        }
