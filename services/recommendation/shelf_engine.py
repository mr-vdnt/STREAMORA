from services.repository.catalog_db import CatalogRepository
from services.recommendation.ranking_engine import RecommendationEngine
import random

class ShelfEngine:
    def __init__(self):
        self.repo = CatalogRepository()
        self.ranker = RecommendationEngine()
        
    def _filter_and_rank(self, items, weights, limit=15, filter_func=None):
        filtered = [item for item in items if filter_func is None or filter_func(item)]
        custom_ranker = RecommendationEngine(custom_weights=weights)
        ranked = custom_ranker.rank_items(filtered)
        return ranked[:limit]
        
    def generate_home_shelves(self, user_id=None, format="all"):
        movies_map = self.repo.get_all()
        movies = list(movies_map.values())
        
        # Filter by format
        if format == "movie":
            movies = [m for m in movies if m.get('content_type') == 'movie']
        elif format == "series":
            movies = [m for m in movies if m.get('content_type') == 'series']

        shelves = []
        
        # 1. 🔥 Everyone in India is watching
        shelves.append({
            "id": "india_trending",
            "title": "🔥 Everyone in India is watching",
            "items": self._filter_and_rank(
                movies, 
                weights={"popularity": 0.4, "indian_popularity": 0.5, "freshness": 0.1, "rating": 0.0, "personalization": 0.0, "engagement": 0.0, "trending_velocity": 0.0, "seasonality": 0.0, "similarity": 0.0}
            )
        })
        
        # 2. 🎬 New this week
        shelves.append({
            "id": "new_releases",
            "title": "🎬 New this week",
            "items": self._filter_and_rank(
                movies, 
                weights={"popularity": 0.2, "indian_popularity": 0.1, "freshness": 0.7, "rating": 0.0, "personalization": 0.0, "engagement": 0.0, "trending_velocity": 0.0, "seasonality": 0.0, "similarity": 0.0}
            )
        })
        
        # 3. 🇮🇳 Bollywood Essentials
        shelves.append({
            "id": "bollywood_essentials",
            "title": "🇮🇳 Bollywood Essentials",
            "items": self._filter_and_rank(
                movies, 
                weights={"popularity": 0.3, "indian_popularity": 0.0, "freshness": 0.0, "rating": 0.7, "personalization": 0.0, "engagement": 0.0, "trending_velocity": 0.0, "seasonality": 0.0, "similarity": 0.0},
                filter_func=lambda m: 'hi' in str(m.get('language', '')).lower() or 'bollywood' in str(m.get('genres', '')).lower()
            )
        })
        
        # 4. 💎 Hidden Gems
        shelves.append({
            "id": "hidden_gems",
            "title": "💎 Hidden Gems",
            "items": self._filter_and_rank(
                movies, 
                weights={"popularity": -0.5, "indian_popularity": 0.0, "freshness": 0.0, "rating": 1.0, "personalization": 0.0, "engagement": 0.0, "trending_velocity": 0.0, "seasonality": 0.0, "similarity": 0.0}
            )
        })
        
        # 5. 🧠 Mind-Bending Sci-Fi
        shelves.append({
            "id": "scifi_mind_bending",
            "title": "🧠 Mind-Bending Sci-Fi",
            "items": self._filter_and_rank(
                movies, 
                weights={"popularity": 0.3, "indian_popularity": 0.0, "freshness": 0.0, "rating": 0.7, "personalization": 0.0, "engagement": 0.0, "trending_velocity": 0.0, "seasonality": 0.0, "similarity": 0.0},
                filter_func=lambda m: 'science fiction' in str(m.get('genres', '')).lower() or 'sci-fi' in str(m.get('genres', '')).lower()
            )
        })
        
        # 6. ❤️ Aurora's Picks (Randomized for now until full personalization is ready)
        aurora_picks = self._filter_and_rank(
            movies, 
            weights={"popularity": 0.2, "indian_popularity": 0.2, "freshness": 0.2, "rating": 0.4, "personalization": 0.0, "engagement": 0.0, "trending_velocity": 0.0, "seasonality": 0.0, "similarity": 0.0}
        )
        random.shuffle(aurora_picks)
        shelves.append({
            "id": "aurora_picks",
            "title": "❤️ Aurora's Picks",
            "items": aurora_picks[:15]
        })
        
        # Determine Hero item (usually the top trending Indian item)
        hero = shelves[0]["items"][0] if shelves[0]["items"] else (movies[0] if movies else {})
        
        return {
            "hero": hero,
            "sections": [s for s in shelves if len(s["items"]) > 0]
        }
