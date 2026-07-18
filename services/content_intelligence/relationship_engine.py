from typing import List, Dict, Set, Tuple
from .graph_store import GraphStore
from .models import EdgeType, GraphEdge, RelationshipConfidence
from .config import GRAPH_CONFIG

class RelationshipEngine:
    """Computes inferred higher-order relationships and similarity confidence."""
    
    def __init__(self, store: GraphStore):
        self.store = store
        
    def infer_movie_relationships(self, movie_id_1: str, movie_id_2: str) -> List[Tuple[EdgeType, float]]:
        """Finds direct shared attributes between two movies."""
        relationships = []
        
        edges1 = self.store.get_edges(movie_id_1)
        edges2 = self.store.get_edges(movie_id_2)
        
        targets1 = {e.target_id: e for e in edges1}
        targets2 = {e.target_id: e for e in edges2}
        
        shared_targets = set(targets1.keys()).intersection(targets2.keys())
        
        has_shared_director = False
        shared_actors = 0
        shared_themes = 0
        
        for t_id in shared_targets:
            edge1 = targets1[t_id]
            
            if edge1.type == EdgeType.DIRECTED_BY:
                has_shared_director = True
            elif edge1.type == EdgeType.ACTED_IN:
                shared_actors += 1
            elif edge1.type == EdgeType.HAS_THEME:
                shared_themes += 1
                
        weights = GRAPH_CONFIG["edge_weights"]
        
        if has_shared_director:
            relationships.append((EdgeType.SHARED_DIRECTOR, weights.get("SHARED_DIRECTOR", 0.9)))
            
        if shared_actors > 0:
            relationships.append((EdgeType.SHARED_ACTOR, min(1.0, shared_actors * weights.get("SHARED_ACTOR", 0.4))))
            
        if shared_themes > 0:
            relationships.append((EdgeType.SHARED_THEME, min(1.0, shared_themes * weights.get("SHARED_THEME", 0.5))))
            
        return relationships
        
    def calculate_similarity(self, movie_id_1: str, movie_id_2: str) -> RelationshipConfidence:
        """Calculates a weighted similarity score between two movies based on shared graph attributes."""
        relationships = self.infer_movie_relationships(movie_id_1, movie_id_2)
        
        if not relationships:
            return RelationshipConfidence(score=0.0, confidence=1.0)
            
        total_score = sum(weight for _, weight in relationships)
        
        # Normalize roughly (0 to 1)
        normalized_score = min(1.0, total_score / 2.0)
        
        # Confidence increases with more shared edges
        confidence = min(1.0, len(relationships) * 0.3 + 0.4)
        
        return RelationshipConfidence(score=normalized_score, confidence=confidence)
