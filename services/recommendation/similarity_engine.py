from services.content_intelligence.embedding_engine import EmbeddingEngine
from services.repository.catalog_db import CatalogRepository
from services.recommendation.ranking_engine import RecommendationEngine

class SimilarityEngine:
    def __init__(self):
        self.embedder = EmbeddingEngine()
        self.repo = CatalogRepository()
        self.ranker = RecommendationEngine()
        
    def get_similar_items(self, item_id: int, top_k: int = 15, multi_shelf: bool = False) -> list:
        """
        Retrieves similar items using the FAISS semantic index and metadata overlap.
        If multi_shelf is True, returns a list of shelf dicts instead of a flat list.
        """
        seed_item = self.repo.get_by_id(item_id)
        if not seed_item:
            return []
            
        seed_text = f"{seed_item.get('title', '')} {seed_item.get('genres', '')} {seed_item.get('director', '')} {seed_item.get('overview', '')}"
        
        # Pull top 50 semantic candidates from FAISS
        candidates_raw = self.embedder.search_similar(seed_text, top_k=50)
        
        seed_director = str(seed_item.get('director', '')).lower()
        seed_type = seed_item.get('content_type', 'movie')
        
        candidates = []
        same_director = []
        same_franchise = []
        
        for cid, distance in candidates_raw:
            if cid == item_id:
                continue
                
            cand = self.repo.get_by_id(cid)
            if not cand:
                continue
                
            if cand.get('content_type', 'movie') != seed_type:
                continue
                
            cand_dict = dict(cand)
            
            # Simple context for the ranker
            ctx = {
                "similarity": max(0, 1.0 - distance/2.0),
                "same_director": 1.0 if seed_director and seed_director != 'unknown' and seed_director == str(cand.get('director', '')).lower() else 0.0
            }
            cand_dict['similarity_score'] = ctx['similarity']
            cand_dict['context'] = ctx
            candidates.append(cand_dict)
            
            if ctx["same_director"] > 0:
                same_director.append(cand_dict)
                
        # Rank the candidates using the global ranker
        context_map = {c['item_id']: c['context'] for c in candidates}
        ranked_candidates = self.ranker.rank_items(candidates, contexts=context_map)
        
        if not multi_shelf:
            return ranked_candidates[:top_k]
            
        # Build shelves
        shelves = []
        
        if ranked_candidates:
            shelves.append({
                "title": "Top Semantic Matches",
                "items": ranked_candidates[:top_k]
            })
            
        if same_director and seed_director and seed_director != 'unknown':
            # Rank same director matches as well
            dir_context_map = {c['item_id']: c['context'] for c in same_director}
            ranked_dir = self.ranker.rank_items(same_director, contexts=dir_context_map)
            shelves.append({
                "title": f"From {seed_item.get('director', 'this director')}",
                "items": ranked_dir[:10]
            })
            
        # Could add "Shared Universe" or "Indian Audience Favorites" here later
        
        return shelves
