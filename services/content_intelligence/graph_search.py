from typing import List, Dict, Set, Optional
from .graph_store import GraphStore
from .models import EdgeType, NodeType
from .relationship_engine import RelationshipEngine
from .graph_cache import GraphCache

class GraphSearchEngine:
    """Executes semantic traversals over the knowledge graph."""
    
    def __init__(self, store: GraphStore, relationship_engine: RelationshipEngine, cache: GraphCache):
        self.store = store
        self.relationship_engine = relationship_engine
        self.cache = cache
        
    def find_related_movies(self, movie_id: str, limit: int = 10) -> List[str]:
        """Finds structurally related movies using 2-hop traversals."""
        # movie -> attribute -> movie
        
        # Check cache
        cache_key = hash(movie_id) # Using simple hash for demo
        cached = self.cache.get_related_movies(cache_key)
        if cached:
            return [f"movie:{c}" for c in cached][:limit]
            
        if not self.store.node_exists(movie_id):
            return []
            
        edges = self.store.get_edges(movie_id)
        related_counts: Dict[str, float] = {}
        
        for edge in edges:
            attr_id = edge.target_id
            attr_node = self.store.get_node(attr_id)
            if not attr_node:
                continue
                
            # Hop back to movies sharing this attribute
            reverse_edges = self.store.get_edges(attr_id)
            for rev_edge in reverse_edges:
                related_movie_id = rev_edge.target_id
                if related_movie_id == movie_id:
                    continue # Skip self
                    
                target_node = self.store.get_node(related_movie_id)
                if target_node and target_node.type == NodeType.MOVIE:
                    weight = edge.weight * rev_edge.weight
                    related_counts[related_movie_id] = related_counts.get(related_movie_id, 0.0) + weight
                    
        # Sort by accumulated edge weight
        sorted_related = sorted(related_counts.items(), key=lambda x: x[1], reverse=True)
        top_ids = [m_id for m_id, _ in sorted_related[:limit]]
        
        # Cache as ints
        try:
            int_ids = [int(m_id.split(":")[1]) for m_id in top_ids]
            self.cache.set_related_movies(cache_key, int_ids)
        except Exception:
            pass
            
        return top_ids
        
    def find_shared_directors(self, movie_id_1: str, movie_id_2: str) -> List[str]:
        return self._find_shared_attributes(movie_id_1, movie_id_2, EdgeType.DIRECTED_BY)
        
    def find_shared_actors(self, movie_id_1: str, movie_id_2: str) -> List[str]:
        return self._find_shared_attributes(movie_id_1, movie_id_2, EdgeType.ACTED_IN)
        
    def find_shared_themes(self, movie_id_1: str, movie_id_2: str) -> List[str]:
        return self._find_shared_attributes(movie_id_1, movie_id_2, EdgeType.HAS_THEME)
        
    def _find_shared_attributes(self, m1: str, m2: str, edge_type: EdgeType) -> List[str]:
        edges1 = self.store.get_edges(m1, edge_type)
        edges2 = self.store.get_edges(m2, edge_type)
        
        t1 = {e.target_id for e in edges1}
        t2 = {e.target_id for e in edges2}
        
        shared_ids = t1.intersection(t2)
        names = []
        for s_id in shared_ids:
            node = self.store.get_node(s_id)
            if node:
                names.append(node.name)
        return names
        
    def get_graph_similarity(self, content_id_1: int, content_id_2: int) -> float:
        cached = self.cache.get_similarity(content_id_1, content_id_2)
        if cached >= 0:
            return cached
            
        m1 = f"movie:{content_id_1}"
        m2 = f"movie:{content_id_2}"
        
        if not self.store.node_exists(m1) or not self.store.node_exists(m2):
            return 0.0
            
        rel_conf = self.relationship_engine.calculate_similarity(m1, m2)
        score = rel_conf.score * rel_conf.confidence
        
        self.cache.set_similarity(content_id_1, content_id_2, score)
        return score
