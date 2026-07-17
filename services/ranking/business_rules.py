class BusinessRuleEngine:
    """Enforces hard business rules before feature extraction and scoring."""
    
    def __init__(self, movies_db: dict):
        self.movies_db = movies_db
        
    def filter(self, candidates: list, query_contract: dict) -> list:
        # Phase 4 already did some hard filtering (year, runtime), but we do a final pass.
        # Most importantly, we must remove the reference_title.
        ref_title = query_contract.get("reference_title")
        ref_id = None
        if ref_title:
            for iid, m in self.movies_db.items():
                if str(m.get("title", "")).lower() == ref_title.lower():
                    ref_id = iid
                    break
                    
        valid_candidates = []
        seen_ids = set()
        
        for c in candidates:
            cid = c["content_id"]
            
            # Rule 1: Deduplication
            if cid in seen_ids:
                continue
                
            # Rule 2: Remove Reference Movie
            if cid == ref_id:
                continue
                
            # Rule 3: Valid Metadata (must exist in DB)
            if cid not in self.movies_db:
                continue
                
            seen_ids.add(cid)
            valid_candidates.append(c)
            
        return valid_candidates
