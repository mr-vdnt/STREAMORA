import os
import sys
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from services.repository.catalog_db import CatalogRepository, Content
from services.recommendation.ranking_engine import RecommendationEngine

from services.repository.catalog_db import (
    CatalogRepository, Content, ContentMetadata, ContentArtwork, ContentStatistics
)

class HeroService:
    """
    Dedicated Service for Hero Content Intelligence & Selection.
    Pipeline: Candidate Retrieval -> Hero Ranking -> Artwork Validation -> Context Boost -> Final Hero
    """
    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()
        self.ranker = RecommendationEngine(custom_weights={
            "PopularityScorer": 0.8,
            "QualityScorer": 0.6,
            "FreshnessScorer": 0.4,
            "RegionalScorer": 0.5
        })

    def select_hero(self, session: Session, format: str = "all", context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        context = context or {}
        
        # 1. Candidate Retrieval (Top 25 highly rated/popular items from canonical schema)
        query = session.query(Content).join(Content.statistics_rel).filter(Content.is_deleted == False)
        if format == "movie":
            query = query.filter(Content.entity_type == 'movie')
        elif format == "series":
            query = query.filter(Content.entity_type == 'tvseries')
            
        query = query.order_by(desc(ContentStatistics.popularity)).limit(25)
        raw_candidates = query.all()
        
        if not raw_candidates:
            return None
            
        candidates = []
        for item in raw_candidates:
            meta = item.metadata_rel
            art = item.artwork_rel
            stats = item.statistics_rel
            c_dict = {
                "id": item.id,
                "uuid": item.uuid,
                "slug": item.slug,
                "entity_type": item.entity_type,
                "title": meta.title if meta else "",
                "original_title": meta.original_title if meta else "",
                "overview": meta.overview if meta else "",
                "tagline": meta.tagline if meta else "",
                "release_date": meta.release_date if meta else "",
                "runtime": meta.runtime if meta else 0,
                "poster_url": art.poster_url if art else None,
                "backdrop_url": art.backdrop_url if art else None,
                "rating": stats.average_rating if stats else 0.0,
                "popularity": stats.popularity if stats else 0.0,
                "genres": [cg.genre.name for cg in item.genres_rel if cg.genre] if hasattr(item, 'genres_rel') and item.genres_rel else [],
            }
            candidates.append(c_dict)
        
        # 2. Hero Ranking via Scorer Pipeline
        scored_candidates = []
        for c in candidates:
            c['item_id'] = c.get('id', 0)
            score = self.ranker.score_item(c, context)
            
            # 3. Artwork Validation (Must have valid backdrop)
            has_backdrop = bool(c.get('backdrop_url') and str(c.get('backdrop_url')).startswith('http'))
            if not has_backdrop:
                score *= 0.1 # Heavily penalize missing artwork
                
            # 4. Context Boost (Match genre or language if in context)
            target_genre = context.get('genre')
            if target_genre and target_genre.lower() in str(c.get('genres', '')).lower():
                score += 1.5
                
            c['hero_score'] = score
            scored_candidates.append((c, score))
            
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        best_hero = scored_candidates[0][0] if scored_candidates else None
        
        if best_hero:
            best_hero['hero_insights'] = {
                "tagline": best_hero.get('tagline') or f"Featured Streamora {best_hero.get('entity_type', 'title').capitalize()}",
                "confidence_score": round(min(0.99, 0.85 + (best_hero.get('rating', 8.0) / 100.0)), 2),
                "selection_reason": f"Top ranked {best_hero.get('entity_type', 'content')} based on global popularity ({best_hero.get('popularity')}) & user affinity."
            }
            
        return best_hero
