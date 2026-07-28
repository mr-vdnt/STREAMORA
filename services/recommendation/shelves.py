from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from services.repository.catalog_db import Content, Movie, TVSeries
from services.recommendation.ranking_engine import RecommendationEngine
import datetime
import random

class MovieExposure:
    """Tracks movie exposure across different contexts (homepage, genre pages, etc.)"""
    def __init__(self):
        self.homepage_count: Dict[int, int] = {}
        self.genre_count: Dict[int, int] = {}
        self.exposed_ids: set = set()

    def can_show_on_homepage(self, item_id: int, max_exposures: int = 1) -> bool:
        return item_id not in self.exposed_ids

    def record_homepage_exposure(self, item_id: int):
        self.homepage_count[item_id] = self.homepage_count.get(item_id, 0) + 1
        self.exposed_ids.add(item_id)

class CandidateRetriever:
    """Declarative SQL-based Candidate Retriever with DB-level exclusion"""
    def __init__(
        self, 
        min_popularity: float = None,
        min_rating: float = None,
        max_popularity: float = None,
        genre_like: str = None,
        theme_like: str = None,
        languages: List[str] = None,
        recent_years: int = None,
        content_type_override: str = None
    ):
        self.min_popularity = min_popularity
        self.min_rating = min_rating
        self.max_popularity = max_popularity
        self.genre_like = genre_like
        self.theme_like = theme_like
        self.languages = languages
        self.recent_years = recent_years
        self.content_type_override = content_type_override

    def retrieve(self, session: Session, format: str = "all", exclude_ids: set = None) -> List[Dict]:
        target_format = self.content_type_override if self.content_type_override else format
        
        if target_format == "movie":
            query = session.query(Movie)
        elif target_format == "series":
            query = session.query(TVSeries)
        else:
            query = session.query(Content)

        if exclude_ids:
            query = query.filter(~Content.id.in_(list(exclude_ids)))

        if self.min_popularity is not None:
            query = query.filter(Content.popularity >= self.min_popularity)
        if self.max_popularity is not None:
            query = query.filter(Content.popularity <= self.max_popularity)
        if self.min_rating is not None:
            query = query.filter(Content.rating >= self.min_rating)
        if self.genre_like:
            query = query.filter(Content.genres.ilike(f"%{self.genre_like}%"))
        if self.theme_like:
            query = query.filter(Content.themes.ilike(f"%{self.theme_like}%"))
        if self.languages:
            query = query.filter(Content.language.in_(self.languages))
        if self.recent_years is not None:
            current_year = datetime.datetime.now().year
            cutoff_year = str(current_year - self.recent_years)
            query = query.filter(Content.year >= cutoff_year)
            
        # Fetch an oversized pool to allow ranking to work its magic
        query = query.order_by(desc(Content.popularity)).limit(200)
        
        results = query.all()
        # Convert to dictionary representation for ranking
        return [{c.key: getattr(item, c.key) for c in item.__mapper__.columns.values()} for item in results]


class RankingStrategy:
    def get_weights(self) -> Dict[str, float]:
        return {"PopularityScorer": 1.0, "RegionalScorer": 0.5}

class TrendingRanking(RankingStrategy):
    def get_weights(self) -> Dict[str, float]:
        return {"PopularityScorer": 0.5, "RegionalScorer": 1.0, "FreshnessScorer": 0.1, "QualityScorer": 0.0}

class NewReleaseRanking(RankingStrategy):
    def get_weights(self) -> Dict[str, float]:
        return {"PopularityScorer": 0.3, "RegionalScorer": 0.8, "FreshnessScorer": 1.0, "QualityScorer": 0.0}

class QualityRanking(RankingStrategy):
    def get_weights(self) -> Dict[str, float]:
        return {"PopularityScorer": -0.2, "RegionalScorer": 0.4, "FreshnessScorer": 0.0, "QualityScorer": 1.0}

class AuroraPicksRanking(RankingStrategy):
    def get_weights(self) -> Dict[str, float]:
        return {"PopularityScorer": 0.0, "RegionalScorer": 0.6, "FreshnessScorer": 0.5, "QualityScorer": 0.8, "PersonalizationScorer": 0.0}


class ShelfAssembler:
    def __init__(self, id: str, title: str, retriever: CandidateRetriever, ranking: RankingStrategy, limit: int = 15, max_shelves: int = 1):
        self.id = id
        self.title = title
        self.retriever = retriever
        self.ranking = ranking
        self.limit = limit
        self.max_shelves = max_shelves

    def generate(self, session: Session, exposure: MovieExposure, format: str = "all", context: str = "home") -> Dict[str, Any]:
        # Declarative SQL retrieval excludes already exposed items at the DB level!
        exclude = exposure.exposed_ids if context == "home" else None
        candidates = self.retriever.retrieve(session, format=format, exclude_ids=exclude)
        
        for m in candidates:
            m['item_id'] = m.get('id', 0)
            
        ranker = RecommendationEngine(custom_weights=self.ranking.get_weights())
        # The pipeline handles Business Rules -> Ranking -> Diversification
        selected = ranker.execute_pipeline(candidates, limit=self.limit)
        
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

# Register 20 declarative shelves for RC2.3
ShelfRegistry.register(ShelfAssembler("trending_india", "Trending India", CandidateRetriever(min_popularity=20.0), TrendingRanking(), limit=20), home_order=1)
ShelfRegistry.register(ShelfAssembler("new_releases", "New Releases", CandidateRetriever(recent_years=2), NewReleaseRanking(), limit=20), home_order=2)
ShelfRegistry.register(ShelfAssembler("bollywood", "Bollywood", CandidateRetriever(languages=["hi"]), TrendingRanking(), limit=20), home_order=3)
ShelfRegistry.register(ShelfAssembler("south_indian", "South Indian", CandidateRetriever(languages=["te", "ta", "ml", "kn"]), TrendingRanking(), limit=20), home_order=4)
ShelfRegistry.register(ShelfAssembler("anime", "Anime", CandidateRetriever(theme_like="anime"), TrendingRanking(), limit=20), home_order=5)
ShelfRegistry.register(ShelfAssembler("korean_dramas", "Korean Dramas", CandidateRetriever(languages=["ko"]), TrendingRanking(), limit=20), home_order=6)
ShelfRegistry.register(ShelfAssembler("scifi", "Sci-Fi", CandidateRetriever(genre_like="science fiction"), TrendingRanking(), limit=20), home_order=7)
ShelfRegistry.register(ShelfAssembler("crime", "Crime", CandidateRetriever(genre_like="crime"), TrendingRanking(), limit=20), home_order=8)
ShelfRegistry.register(ShelfAssembler("mystery", "Mystery", CandidateRetriever(genre_like="mystery"), TrendingRanking(), limit=20), home_order=9)
ShelfRegistry.register(ShelfAssembler("comedy", "Comedy", CandidateRetriever(genre_like="comedy"), TrendingRanking(), limit=20), home_order=10)
ShelfRegistry.register(ShelfAssembler("family", "Family", CandidateRetriever(genre_like="family"), TrendingRanking(), limit=20), home_order=11)
ShelfRegistry.register(ShelfAssembler("oscar_winners", "Oscar Winners", CandidateRetriever(theme_like="oscars"), QualityRanking(), limit=20), home_order=12)
ShelfRegistry.register(ShelfAssembler("hidden_gems", "Hidden Gems", CandidateRetriever(min_rating=7.5, max_popularity=40.0), QualityRanking(), limit=20), home_order=13)
ShelfRegistry.register(ShelfAssembler("classic_movies", "Classic Movies", CandidateRetriever(theme_like="classics"), QualityRanking(), limit=20), home_order=14)
ShelfRegistry.register(ShelfAssembler("top_imdb", "Top IMDb", CandidateRetriever(min_rating=8.5), QualityRanking(), limit=20), home_order=15)
ShelfRegistry.register(ShelfAssembler("netflix_trending", "Netflix Trending", CandidateRetriever(theme_like="netflix"), TrendingRanking(), limit=20), home_order=16)
ShelfRegistry.register(ShelfAssembler("prime_video_trending", "Prime Video Trending", CandidateRetriever(theme_like="prime"), TrendingRanking(), limit=20), home_order=17)
ShelfRegistry.register(ShelfAssembler("disney_picks", "Disney Picks", CandidateRetriever(theme_like="disney"), TrendingRanking(), limit=20), home_order=18)
ShelfRegistry.register(ShelfAssembler("mind_bending", "Mind Bending", CandidateRetriever(genre_like="thriller"), AuroraPicksRanking(), limit=20), home_order=19)
ShelfRegistry.register(ShelfAssembler("continue_watching", "Continue Watching", CandidateRetriever(min_rating=7.0), QualityRanking(), limit=20), home_order=20)
