from typing import List, Dict, Any
from services.repository.catalog_db import CatalogRepository
from services.recommendation.shelves import ShelfRegistry, MovieExposure
import random
import datetime

class ShelfEngine:
    def __init__(self):
        self.repo = CatalogRepository()
        
    def _calculate_hero_score(self, m: Dict[str, Any]) -> float:
        # Default config per user's specifications
        cfg = {
            "popularity": 0.30,
            "freshness": 0.15,
            "artwork": 0.20,
            "trailer": 0.10,
            "indian_popularity": 0.15,
            "quality": 0.10
        }
        
        pop = float(m.get('popularity', 0)) / 100.0  # normalize
        ind_pop = pop * 1.5 if "hi" in str(m.get('language', '')).lower() else pop * 0.5
        rating = float(m.get('rating', 0)) / 10.0
        
        # Freshness
        year_str = str(m.get('year', ''))
        freshness = 0.0
        try:
            age = datetime.datetime.now().year - int(year_str)
            if age <= 1: freshness = 1.0
            elif age <= 3: freshness = 0.7
            elif age <= 10: freshness = 0.3
        except:
            pass
            
        artwork = 1.0 if m.get('backdrop_url') else 0.0
        trailer = 1.0 if m.get('trailer_url') else 0.0
        
        return (pop * cfg["popularity"] +
                freshness * cfg["freshness"] +
                artwork * cfg["artwork"] +
                trailer * cfg["trailer"] +
                ind_pop * cfg["indian_popularity"] +
                rating * cfg["quality"])

    def get_top_heroes(self, movies: List[Dict], count=5) -> List[Dict]:
        if not movies:
            return []
        # Sort by hero score
        scored = sorted(movies, key=self._calculate_hero_score, reverse=True)
        return scored[:count]

    def generate_home_shelves(self, user_id=None, format="all") -> Dict[str, Any]:
        movies_map = self.repo.get_all()
        movies = list(movies_map.values())
        
        # Filter by format
        if format == "movie":
            movies = [m for m in movies if m.get('content_type') == 'movie']
        elif format == "series":
            movies = [m for m in movies if m.get('content_type') == 'series']

        exposure = MovieExposure()
        shelves = []
        
        # Use ShelfRegistry to get the shelves in home_order
        assemblers = ShelfRegistry.get_home_shelves()
        for assembler in assemblers:
            shelf_data = assembler.generate(movies, exposure, context="home")
            if shelf_data["items"]:
                shelves.append(shelf_data)
        
        top_heroes = self.get_top_heroes(movies, count=10)
        
        return {
            "top_heroes": top_heroes,
            "sections": shelves
        }
        
    def generate_genre_shelves(self, genre: str, user_id=None) -> Dict[str, Any]:
        movies_map = self.repo.get_all()
        all_movies = list(movies_map.values())
        
        genre_movies = [m for m in all_movies if genre.lower() in str(m.get('genres', '')).lower()]
        exposure = MovieExposure()
        
        # Define temporary assemblers for the genre page
        from services.recommendation.shelves import (
            ShelfAssembler, TrendingRetriever, TrendingRanking, NewReleaseRetriever, 
            NewReleaseRanking, HiddenGemsRetriever, QualityRanking
        )
        
        assemblers = [
            ShelfAssembler("trending_genre", f"🔥 Trending {genre.title()}", TrendingRetriever(), TrendingRanking(), limit=15, max_shelves=2),
            ShelfAssembler("new_genre", f"🎬 New in {genre.title()}", NewReleaseRetriever(), NewReleaseRanking(), limit=15, max_shelves=2),
            ShelfAssembler("hidden_genre", f"💎 Hidden {genre.title()} Gems", HiddenGemsRetriever(), QualityRanking(), limit=15, max_shelves=1)
        ]
        
        shelves = []
        for assembler in assemblers:
            shelf_data = assembler.generate(genre_movies, exposure, context="genre")
            if shelf_data["items"]:
                shelves.append(shelf_data)
                
        top_heroes = self.get_top_heroes(genre_movies, count=5)
        
        return {
            "top_heroes": top_heroes,
            "sections": shelves,
            "metadata": {
                "genre": genre,
                "total_items": len(genre_movies)
            }
        }
