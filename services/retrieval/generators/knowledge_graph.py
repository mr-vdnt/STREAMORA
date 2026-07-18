from typing import List, Dict, Any, Optional
from .base import CandidateGenerator
from services.content_intelligence.adapter import ContentIntelligenceAdapter

class KnowledgeGraphGenerator(CandidateGenerator):
    """Retrieves candidates based on knowledge graph traversals (e.g. shared entities)."""
    
    def __init__(self, movies_db: Dict[int, Any], adapter: ContentIntelligenceAdapter):
        self.movies_db = movies_db
        self.adapter = adapter
        
    @property
    def name(self) -> str:
        return "KnowledgeGraph"

    def retrieve(self, query_contract: dict) -> List[Dict[str, Any]]:
        # This generator typically needs a seed content_id to traverse from.
        # Check reference_title to resolve seed ID
        seed_ids = []
        ref_title = query_contract.get("reference_title")
        if ref_title:
            for iid, m in self.movies_db.items():
                if str(m.get("title", "")).lower() == ref_title.lower():
                    seed_ids.append(iid)
                    break
                    
        # Or if "seed_ids" is directly in context (for tests)
        if not seed_ids and "seed_ids" in query_contract:
            seed_ids = query_contract["seed_ids"]
            
        if not seed_ids:
            return []
            
        candidates = self.adapter.get_similar_candidates(seed_ids, limit=10)
        
        # Add basic metadata to candidates
        for c in candidates:
            c_id = c["content_id"]
            if c_id in self.movies_db:
                c["generator"] = self.name
                c["title"] = self.movies_db[c_id].get("title", "Unknown")
                c["confidence"] = c.get("score", 0.5)
                
        return candidates
