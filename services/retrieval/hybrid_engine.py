import time
from typing import List, Dict, Any
from .registry import GeneratorRegistry
from .models import Candidate, RetrievalContext, RetrievalMetadata, GeneratorMetadata

class HybridRetrievalEngine:
    def __init__(self, registry: GeneratorRegistry, movies_db: dict):
        self.registry = registry
        self.movies_db = movies_db
        
    def _passes_hard_filters(self, content_id: int, filters: dict) -> bool:
        movie = self.movies_db.get(content_id)
        if not movie:
            return False
            
        if "year_min" in filters:
            try:
                if int(movie.get('year', 0)) < filters["year_min"]: return False
            except ValueError: return False
            
        if "year_max" in filters:
            try:
                if int(movie.get('year', 0)) > filters["year_max"]: return False
            except ValueError: return False
            
        if "runtime_max" in filters:
            try:
                if int(movie.get('runtime', 0)) > filters["runtime_max"]: return False
            except ValueError: return False
            
        if "exclude_genres" in filters:
            movie_genres = set([g.strip().lower() for g in str(movie.get('genres', '')).split('|')])
            exclude = set([g.lower() for g in filters["exclude_genres"]])
            if movie_genres.intersection(exclude):
                return False
                
        return True

    def generate_candidates(self, query_contract: dict) -> Dict[str, Any]:
        start_time = time.time()
        
        # 1. Setup
        fingerprint = query_contract.get("fingerprint", "UNKNOWN")
        filters = query_contract.get("filters", {})
        ref_title = query_contract.get("reference_title")
        ref_id = None
        
        # Resolve reference title to ID if present, so we can exclude it from results
        if ref_title:
            for iid, m in self.movies_db.items():
                if str(m.get('title', '')).lower() == ref_title.lower():
                    ref_id = iid
                    break
        
        all_candidates_by_generator = {}
        diagnostics = []
        
        # 2. Generator Selection / Planner (simple logic for now)
        active_generators = self.registry.get_all()
        
        # 3. Execution
        for gen in active_generators:
            gen_start = time.time()
            try:
                raw_candidates = gen.retrieve(query_contract)
            except Exception as e:
                print(f"Generator {gen.name} failed: {e}")
                raw_candidates = []
                
            # Filter and Validate
            valid_candidates = []
            for c in raw_candidates:
                cid = c["content_id"]
                if cid == ref_id: continue # Exclude reference item itself
                if self._passes_hard_filters(cid, filters):
                    valid_candidates.append(c)
                    
            all_candidates_by_generator[gen.name] = valid_candidates
            
            gen_latency = int((time.time() - gen_start) * 1000)
            diagnostics.append({
                "generator": gen.name,
                "latency_ms": gen_latency,
                "candidate_count": len(valid_candidates)
            })
            
        # 4. RRF Merging (k=60)
        K = 60
        rrf_scores = {}
        generator_provenance = {}
        
        for gen_name, candidates in all_candidates_by_generator.items():
            for c in candidates:
                cid = c["content_id"]
                rank = c.get("rank", 100)
                score = c.get("score", 0.0)
                
                if cid not in rrf_scores:
                    rrf_scores[cid] = 0.0
                    generator_provenance[cid] = []
                    
                rrf_scores[cid] += 1.0 / (K + rank)
                generator_provenance[cid].append(
                    GeneratorMetadata(name=gen_name, rank=rank, score=score)
                )
                
        # 5. Build Output Candidates
        final_candidates = []
        context = RetrievalContext(fingerprint=fingerprint, catalog_version=1)
        
        for cid, rrf in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True):
            meta = RetrievalMetadata(
                generators=generator_provenance[cid],
                fusion_score=rrf
            )
            final_candidates.append(
                Candidate(content_id=cid, retrieval=meta, context=context)
            )
            
        total_latency = int((time.time() - start_time) * 1000)
        
        return {
            "query_fingerprint": fingerprint,
            "retrieval_metadata": {
                "catalog_version": 1,
                "retrieval_time_ms": total_latency
            },
            "diagnostics": diagnostics,
            "candidates": [c.model_dump() for c in final_candidates[:20]]
        }
