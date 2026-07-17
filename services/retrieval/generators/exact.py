from typing import List, Dict, Any
from .base import CandidateGenerator

class ExactSearchGenerator(CandidateGenerator):
    """
    Candidate Generator that performs deterministic metadata matching
    using the engine built in Phase 2.
    """
    
    def __init__(self, search_engine):
        self.search_engine = search_engine

    @property
    def name(self) -> str:
        return "exact"

    def retrieve(self, query_contract: dict) -> List[Dict[str, Any]]:
        # Map the V1.0 query contract back to a raw text string for the Phase 2 engine,
        # or interact with it directly.
        # Since Phase 2 engine extracts entities itself, we just pass the text representation
        # of the known entities to trigger deterministic rules.
        
        entities = query_contract.get("entities", {})
        parts = []
        if query_contract.get("reference_title"):
            parts.append(query_contract["reference_title"])
        parts.extend(entities.get("actors", []))
        parts.extend(entities.get("directors", []))
        parts.extend(entities.get("genres", []))
        parts.extend(entities.get("themes", []))
        
        query_text = " ".join(parts)
        if not query_text:
            return []
            
        results = self.search_engine.search(query_text, limit=15)
        
        candidates = []
        for idx, res in enumerate(results):
            candidates.append({
                "content_id": res["item_id"],
                "score": res.get("match_percentage", 100) / 100.0,
                "rank": idx + 1
            })
            
        return candidates
