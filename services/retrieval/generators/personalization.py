from typing import List, Dict, Any
from .base import CandidateGenerator

class PersonalizationGenerator(CandidateGenerator):
    """Retrieves candidates based on the user's strong preferences."""
    
    def __init__(self, db_connector: Any, personalization_adapter: Any):
        self.db = db_connector
        self.adapter = personalization_adapter
        
    @property
    def name(self) -> str:
        return "PersonalizationGenerator"
        
    def retrieve(self, query_contract: dict) -> List[Dict[str, Any]]:
        # The query contract should contain the user_id
        user_id = query_contract.get("user_id")
        if not user_id:
            return []
            
        prefs = self.adapter.get_preferred_directors_and_actors(user_id)
        directors = prefs.get("directors", [])
        
        candidates = []
        if not directors:
            return candidates
            
        # Very simple fallback: scan DB for the top preferred director
        for iid, movie in self.db.items():
            movie_dir = str(movie.get("director", ""))
            if any(d in movie_dir for d in directors):
                candidates.append({"content_id": iid, "score": 0.8})
                if len(candidates) >= 5: # Limit candidates to avoid noise
                    break
                    
        return candidates
