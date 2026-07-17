from typing import List
from abc import ABC, abstractmethod
from .models import Recommendation
from .config.diversity import DIVERSITY_LIMITS

class DiversityPolicy(ABC):
    @abstractmethod
    def apply(self, recommendations: List[Recommendation], movies_db: dict) -> List[Recommendation]:
        pass

class FranchiseDiversityPolicy(DiversityPolicy):
    def apply(self, recommendations: List[Recommendation], movies_db: dict) -> List[Recommendation]:
        limit = DIVERSITY_LIMITS.get("MAX_SAME_FRANCHISE", 2)
        franchise_counts = {}
        filtered = []
        
        for rec in recommendations:
            movie = movies_db.get(rec.content_id, {})
            franchise = movie.get("franchise")
            
            if franchise:
                count = franchise_counts.get(franchise, 0)
                if count >= limit:
                    continue
                franchise_counts[franchise] = count + 1
                
            filtered.append(rec)
            
        return filtered

class DirectorDiversityPolicy(DiversityPolicy):
    def apply(self, recommendations: List[Recommendation], movies_db: dict) -> List[Recommendation]:
        limit = DIVERSITY_LIMITS.get("MAX_SAME_DIRECTOR", 2)
        director_counts = {}
        filtered = []
        
        for rec in recommendations:
            movie = movies_db.get(rec.content_id, {})
            directors = [d.strip().lower() for d in str(movie.get("director", "")).split(",") if d.strip()]
            
            allowed = True
            for d in directors:
                if director_counts.get(d, 0) >= limit:
                    allowed = False
                    break
                    
            if allowed:
                for d in directors:
                    director_counts[d] = director_counts.get(d, 0) + 1
                filtered.append(rec)
                
        return filtered

class DiversityOptimizer:
    def __init__(self):
        self.policies: List[DiversityPolicy] = [
            FranchiseDiversityPolicy(),
            DirectorDiversityPolicy()
        ]
        
    def optimize(self, recommendations: List[Recommendation], movies_db: dict) -> List[Recommendation]:
        current = recommendations
        for policy in self.policies:
            current = policy.apply(current, movies_db)
        return current
