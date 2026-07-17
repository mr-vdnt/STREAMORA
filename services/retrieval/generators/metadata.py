from typing import List, Dict, Any
from .base import CandidateGenerator

class MetadataGenerator(CandidateGenerator):
    """
    Candidate Generator that performs similarity scoring based on
    structured metadata overlap (Genres, Directors, Actors).
    """
    
    def __init__(self, movies_db: dict):
        self.movies_db = movies_db
        
    @property
    def name(self) -> str:
        return "metadata"

    def retrieve(self, query_contract: dict) -> List[Dict[str, Any]]:
        entities = query_contract.get("entities", {})
        target_genres = set([g.lower() for g in entities.get("genres", [])])
        target_actors = set([a.lower() for a in entities.get("actors", [])])
        target_directors = set([d.lower() for d in entities.get("directors", [])])
        
        if not target_genres and not target_actors and not target_directors:
            return []
            
        scored_candidates = []
        for iid, row in self.movies_db.items():
            score = 0.0
            
            # Genre overlap
            movie_genres = set([g.strip().lower() for g in str(row.get('genres', '')).split('|')])
            if target_genres:
                overlap = len(target_genres.intersection(movie_genres))
                score += (overlap / len(target_genres)) * 0.4
                
            # Director overlap
            movie_directors = set([d.strip().lower() for d in str(row.get('director', '')).split(',')])
            if target_directors:
                overlap = len(target_directors.intersection(movie_directors))
                if overlap > 0: score += 0.4
                
            # Actor overlap
            movie_actors = set([a.strip().lower() for a in str(row.get('cast', '')).split(',')])
            if target_actors:
                overlap = len(target_actors.intersection(movie_actors))
                if overlap > 0: score += 0.2
                
            if score > 0:
                scored_candidates.append({
                    "content_id": iid,
                    "score": score
                })
                
        # Sort by score
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        
        # Add rank
        for idx, c in enumerate(scored_candidates[:20]):
            c["rank"] = idx + 1
            
        return scored_candidates[:20]
