from typing import List, Dict, Any
import importlib
import pkgutil

import services.recommendation.scorers as scorers_pkg
from services.recommendation.scorers.base_scorer import BaseScorer

class RecommendationEngine:
    """
    Configurable scoring engine for ranking movies.
    Dynamically loads all scorers from the `scorers` package.
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
                    
                    # Register default weight if not overridden
                    if scorer_instance.name not in self.weights:
                        self.weights[scorer_instance.name] = scorer_instance.default_weight

    def score_item(self, movie: Dict[str, Any], context: Dict[str, Any] = None) -> float:
        """
        Calculates the final score for a movie by aggregating all loaded scorers.
        """
        context = context or {}
        final_score = 0.0
        
        for scorer in self.scorers:
            weight = self.weights.get(scorer.name, 0.0)
            if weight != 0.0:
                raw_score = scorer.score(movie, context)
                final_score += (raw_score * weight)
                
        return final_score

    def rank_items(self, items: list, contexts: dict = None) -> list:
        """
        Ranks a list of movie dictionaries based on the scoring engine.
        `contexts` is a dict mapping item_id -> context_dict.
        """
        contexts = contexts or {}
        
        scored_items = []
        for item in items:
            iid = item.get('item_id')
            ctx = contexts.get(iid, {})
            score = self.score_item(item, ctx)
            scored_items.append((item, score))
            
        # Sort by score descending
        scored_items.sort(key=lambda x: x[1], reverse=True)
        return [item for item, score in scored_items]
