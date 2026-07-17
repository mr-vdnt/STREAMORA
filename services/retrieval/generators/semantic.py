from typing import List, Dict, Any
from .base import CandidateGenerator
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
import os

class SemanticGenerator(CandidateGenerator):
    """
    Candidate Generator that performs vector similarity search
    using FAISS and SentenceTransformers.
    """
    
    def __init__(self, index_path: str, model_name: str = 'all-MiniLM-L6-v2'):
        self._index = None
        self._model = None
        
        if os.path.exists(index_path):
            try:
                self._index = faiss.read_index(index_path)
                self._model = SentenceTransformer(model_name)
            except Exception as e:
                print(f"Failed to load FAISS index: {e}")
                
    @property
    def name(self) -> str:
        return "semantic"

    def retrieve(self, query_contract: dict) -> List[Dict[str, Any]]:
        if not self._index or not self._model:
            return []
            
        entities = query_contract.get("entities", {})
        themes = entities.get("themes", [])
        ref_title = query_contract.get("reference_title")
        
        if not themes and not ref_title:
            # Semantic search is best for vague/thematic queries, not exact actor searches
            if query_contract.get("fingerprint") in ["SEARCH_ACT", "SEARCH_DIR", "SEARCH_ACT_GEN"]:
                return []
                
        # Build semantic search string
        search_terms = []
        if ref_title:
            search_terms.append(f"movies similar to {ref_title}")
        search_terms.extend(themes)
        search_terms.extend(entities.get("genres", []))
        
        query_text = " ".join(search_terms)
        if not query_text:
            return []
            
        query_vector = self._model.encode([query_text]).astype('float32')
        faiss.normalize_L2(query_vector)
        
        distances, indices = self._index.search(query_vector, 20)
        
        candidates = []
        for idx, (dist, iid) in enumerate(zip(distances[0], indices[0])):
            if iid != -1:
                candidates.append({
                    "content_id": int(iid),
                    "score": float(dist), # FAISS inner product distance (higher is better for cosine)
                    "rank": idx + 1
                })
                
        return candidates
