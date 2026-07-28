from typing import List, Dict, Any
from services.repository.catalog_db import CatalogRepository, Content
from services.recommendation.shelves import ShelfRegistry, MovieExposure, CandidateRetriever
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
        exposure = MovieExposure()
        shelves = []
        
        with self.repo.get_session() as session:
            # Use ShelfRegistry to get the shelves in home_order
            assemblers = ShelfRegistry.get_home_shelves()
            for assembler in assemblers:
                shelf_data = assembler.generate(session, exposure, format=format, context="home")
                if shelf_data["items"]:
                    shelves.append(shelf_data)
            
            # Fetch generic popular candidates for heroes
            # We can use a basic CandidateRetriever to get top movies/series
            hero_retriever = CandidateRetriever(min_popularity=10.0)
            hero_candidates = hero_retriever.retrieve(session, format=format)
            top_heroes = self.get_top_heroes(hero_candidates, count=10)
        
        return {
            "top_heroes": top_heroes,
            "sections": shelves
        }
        
    def generate_genre_shelves(self, genre: str, user_id=None) -> Dict[str, Any]:
        exposure = MovieExposure()
        
        # Define temporary assemblers for the genre page
        from services.recommendation.shelves import (
            ShelfAssembler, TrendingRanking, NewReleaseRanking, QualityRanking, CandidateRetriever
        )
        
        assemblers = [
            ShelfAssembler("trending_genre", f"🔥 Trending {genre.title()}", CandidateRetriever(genre_like=genre, min_popularity=10.0), TrendingRanking(), limit=15, max_shelves=2),
            ShelfAssembler("new_genre", f"🎬 New in {genre.title()}", CandidateRetriever(genre_like=genre, recent_years=3), NewReleaseRanking(), limit=15, max_shelves=2),
            ShelfAssembler("hidden_genre", f"💎 Hidden {genre.title()} Gems", CandidateRetriever(genre_like=genre, min_rating=7.5, max_popularity=40.0), QualityRanking(), limit=15, max_shelves=1)
        ]
        
        shelves = []
        with self.repo.get_session() as session:
            for assembler in assemblers:
                shelf_data = assembler.generate(session, exposure, context="genre")
                if shelf_data["items"]:
                    shelves.append(shelf_data)
                    
            hero_retriever = CandidateRetriever(genre_like=genre)
            hero_candidates = hero_retriever.retrieve(session)
            top_heroes = self.get_top_heroes(hero_candidates, count=5)
        
        return {
            "top_heroes": top_heroes,
            "sections": shelves,
            "metadata": {
                "genre": genre,
                "total_items": len(hero_candidates)
            }
        }
