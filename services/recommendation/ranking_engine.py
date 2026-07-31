from typing import List, Dict, Any
import importlib
import pkgutil

import services.recommendation.scorers as scorers_pkg
from services.recommendation.scorers.base_scorer import BaseScorer

class BusinessRules:
    """Applies strict business logic filters before ranking."""
    @staticmethod
    def apply(items: list, context: dict = None) -> list:
        # Example rule: filter out items missing core fields
        return [item for item in items if item.get('title') and item.get('item_id')]

class DiversificationPolicy:
    """Ensures a diverse mix of content in the final output."""
    @staticmethod
    def apply(items: list, limit: int = 15) -> list:
        if not items:
            return []
            
        diversified = []
        seen_genres = set()
        
        for item in items:
            if len(diversified) >= limit:
                break
                
            # Naive diversification: avoid putting too many of the exact same primary genre back to back.
            genres = item.get('genres', '')
            primary_genre = genres.split('|')[0] if genres else ''
            
            # Allow it if we haven't seen this genre recently, or if we are desperate
            if primary_genre not in seen_genres or len(seen_genres) > 5:
                diversified.append(item)
                if primary_genre:
                    seen_genres.add(primary_genre)
            else:
                # If we just saw this genre, we still might add it if we clear the set periodically
                if len(diversified) % 3 == 0:
                    seen_genres.clear()
                diversified.append(item)
                
        # Fill rest if we filtered too aggressively
        if len(diversified) < limit:
            for item in items:
                if len(diversified) >= limit:
                    break
                if item not in diversified:
                    diversified.append(item)
                    
        return diversified

class RecommendationEngine:
    """
    Configurable scoring engine for ranking movies.
    Executes the full pipeline: Business Rules -> Semantic Rank -> Popularity -> Regional Boost -> Diversification
    """
    def __init__(self, custom_weights: Dict[str, float] = None):
        self.scorers: List[BaseScorer] = []
        self.weights: Dict[str, float] = custom_weights or {}
        self._load_scorers()

    def _load_scorers(self):
        """Discovers and instantiates all scorer classes."""
        for _, module_name, _ in pkgutil.iter_modules(scorers_pkg.__path__):
            if module_name == 'base_scorer':
                continue
                
            module = importlib.import_module(f"services.recommendation.scorers.{module_name}")
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, BaseScorer) and attr is not BaseScorer:
                    scorer_instance = attr()
                    self.scorers.append(scorer_instance)
                    
                    if scorer_instance.name not in self.weights:
                        self.weights[scorer_instance.name] = scorer_instance.default_weight

    def score_item(self, movie: Dict[str, Any], context: Dict[str, Any] = None) -> float:
        context = context or {}
        final_score = 0.0
        
        for scorer in self.scorers:
            weight = self.weights.get(scorer.name, 0.0)
            if weight != 0.0:
                raw_score = scorer.score(movie, context)
                final_score += (raw_score * weight)
                
        return final_score

    def execute_pipeline(self, items: list, contexts: dict = None, limit: int = 15) -> list:
        """
        Executes: Business Rules -> Ranking -> Diversification
        Note: Candidate Retrieval and Exposure Policy (home page limit) are handled in shelves.py
        """
        # 1. Business Rules
        filtered_items = BusinessRules.apply(items)
        
        # 2. Score and Rank
        contexts = contexts or {}
        scored_items = []
        for item in filtered_items:
            iid = item.get('item_id')
            ctx = contexts.get(iid, {})
            score = self.score_item(item, ctx)
            item['ranking_score'] = score  # Inject for debugging/UI
            scored_items.append((item, score))
            
        scored_items.sort(key=lambda x: x[1], reverse=True)
        ranked_items = [item for item, score in scored_items]
        
        # 3. Diversification
        diversified_items = DiversificationPolicy.apply(ranked_items, limit=limit)
        
        return diversified_items

    def rank_items(self, items: list, contexts: dict = None, limit: int = 15) -> list:
        """Alias for execute_pipeline to support similarity engine and legacy callers."""
        return self.execute_pipeline(items, contexts=contexts, limit=limit)

