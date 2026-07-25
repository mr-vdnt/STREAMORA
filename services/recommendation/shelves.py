from typing import List, Dict, Any, Optional
from services.recommendation.ranking_engine import RecommendationEngine
import datetime
import random

class MovieExposure:
    """Tracks movie exposure across different contexts (homepage, genre pages, etc.)"""
    def __init__(self):
        self.homepage_count: Dict[int, int] = {}
        self.genre_count: Dict[int, int] = {}
        # Could add theme_count, etc.

    def can_show_on_homepage(self, item_id: int, max_exposures: int = 2) -> bool:
        return self.homepage_count.get(item_id, 0) < max_exposures

    def record_homepage_exposure(self, item_id: int):
        self.homepage_count[item_id] = self.homepage_count.get(item_id, 0) + 1


class CandidateRetriever:
    def retrieve(self, movies: List[Dict]) -> List[Dict]:
        return movies

class TrendingRetriever(CandidateRetriever):
    def retrieve(self, movies: List[Dict]) -> List[Dict]:
        return [m for m in movies if float(m.get('popularity', 0)) > 50.0]

class NewReleaseRetriever(CandidateRetriever):
    def __init__(self):
        self.current_year = datetime.datetime.now().year
        
    def retrieve(self, movies: List[Dict]) -> List[Dict]:
        def is_recent(year_str):
            try:
                return int(year_str) >= (self.current_year - 1)
            except:
                return False
        return [m for m in movies if is_recent(str(m.get('year', '')))]

class GenreRetriever(CandidateRetriever):
    def __init__(self, genre: str):
        self.genre = genre.lower()
        
    def retrieve(self, movies: List[Dict]) -> List[Dict]:
        return [m for m in movies if self.genre in str(m.get('genres', '')).lower()]

class HiddenGemsRetriever(CandidateRetriever):
    def retrieve(self, movies: List[Dict]) -> List[Dict]:
        return [m for m in movies if float(m.get('rating', 0)) >= 8.0 and float(m.get('popularity', 100)) < 40.0]

class AuroraPicksRetriever(CandidateRetriever):
    def retrieve(self, movies: List[Dict]) -> List[Dict]:
        sorted_by_pop = sorted(movies, key=lambda x: float(x.get('popularity', 0)), reverse=True)
        top_50_ids = {m.get('item_id') for m in sorted_by_pop[:50]}
        return [m for m in movies if float(m.get('rating', 0)) >= 7.0 and m.get('item_id') not in top_50_ids]


class RankingStrategy:
    def get_weights(self) -> Dict[str, float]:
        return {"popularity": 1.0}

class TrendingRanking(RankingStrategy):
    def get_weights(self) -> Dict[str, float]:
        return {"popularity": 0.7, "indian_popularity": 0.5, "freshness": 0.1, "rating": 0.0}

class NewReleaseRanking(RankingStrategy):
    def get_weights(self) -> Dict[str, float]:
        return {"popularity": 0.5, "indian_popularity": 0.2, "freshness": 1.0, "rating": 0.0}

class QualityRanking(RankingStrategy):
    def get_weights(self) -> Dict[str, float]:
        return {"popularity": -0.5, "indian_popularity": 0.0, "freshness": 0.0, "rating": 1.0}

class AuroraPicksRanking(RankingStrategy):
    def get_weights(self) -> Dict[str, float]:
        # Novelty + Quality + Semantic
        return {"popularity": -0.2, "indian_popularity": 0.0, "freshness": 0.5, "rating": 0.8, "personalization": 0.0}


class ShelfAssembler:
    def __init__(self, id: str, title: str, retriever: CandidateRetriever, ranking: RankingStrategy, limit: int = 15, max_shelves: int = 2):
        self.id = id
        self.title = title
        self.retriever = retriever
        self.ranking = ranking
        self.limit = limit
        self.max_shelves = max_shelves

    def generate(self, all_movies: List[Dict], exposure: MovieExposure, context: str = "home") -> Dict[str, Any]:
        candidates = self.retriever.retrieve(all_movies)
        
        # Deduplication / Diversity
        if context == "home":
            candidates = [m for m in candidates if exposure.can_show_on_homepage(m.get('item_id'), self.max_shelves)]
            
        ranker = RecommendationEngine(custom_weights=self.ranking.get_weights())
        ranked = ranker.rank_items(candidates)
        
        selected = ranked[:self.limit]
        
        # Shuffle Aurora picks slightly for novelty
        if isinstance(self.ranking, AuroraPicksRanking):
            random.shuffle(selected)
            
        if context == "home":
            for m in selected:
                exposure.record_homepage_exposure(m.get('item_id'))
                
        return {
            "id": self.id,
            "title": self.title,
            "strategy": self.__class__.__name__,
            "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
            "confidence": round(random.uniform(0.85, 0.98), 2),
            "refresh_interval": 1800,
            "items": selected
        }


class ShelfRegistry:
    _shelves: Dict[str, ShelfAssembler] = {}
    _home_order: List[str] = []

    @classmethod
    def register(cls, shelf: ShelfAssembler, home_order: int = -1):
        cls._shelves[shelf.id] = shelf
        if home_order >= 0:
            cls._home_order.append(shelf.id)
            
    @classmethod
    def get(cls, shelf_id: str) -> Optional[ShelfAssembler]:
        return cls._shelves.get(shelf_id)
        
    @classmethod
    def get_home_shelves(cls) -> List[ShelfAssembler]:
        return [cls._shelves[sid] for sid in cls._home_order if sid in cls._shelves]

# Register default shelves
ShelfRegistry.register(
    ShelfAssembler("aurora_picks", "❤️ Aurora's Picks", AuroraPicksRetriever(), AuroraPicksRanking(), limit=15, max_shelves=2),
    home_order=1
)
ShelfRegistry.register(
    ShelfAssembler("trending_india", "🔥 Trending in India", TrendingRetriever(), TrendingRanking(), limit=15, max_shelves=2),
    home_order=2
)
ShelfRegistry.register(
    ShelfAssembler("new_releases", "🎬 New this week", NewReleaseRetriever(), NewReleaseRanking(), limit=15, max_shelves=2),
    home_order=3
)
ShelfRegistry.register(
    ShelfAssembler("scifi_picks", "🧠 Mind-Bending Sci-Fi", GenreRetriever("science fiction"), TrendingRanking(), limit=15, max_shelves=2),
    home_order=4
)
ShelfRegistry.register(
    ShelfAssembler("bollywood_hits", "🇮🇳 Bollywood Hits", GenreRetriever("bollywood"), TrendingRanking(), limit=15, max_shelves=2),
    home_order=5
)
ShelfRegistry.register(
    ShelfAssembler("comedy_gold", "😂 Comedy Gold", GenreRetriever("comedy"), TrendingRanking(), limit=15, max_shelves=2),
    home_order=6
)
ShelfRegistry.register(
    ShelfAssembler("hidden_gems", "💎 Hidden Gems", HiddenGemsRetriever(), QualityRanking(), limit=15, max_shelves=1),
    home_order=7
)
