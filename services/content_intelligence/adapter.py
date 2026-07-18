from typing import Dict, Any, List, Optional
from .graph_store import InMemoryGraphStore
from .graph_builder import KnowledgeGraphBuilder
from .graph_search import GraphSearchEngine
from .relationship_engine import RelationshipEngine
from .graph_cache import GraphCache
from .models import EdgeType

class ContentIntelligenceAdapter:
    """The only public interface for Content Intelligence."""
    
    def __init__(self, movies_db: Dict[int, Any]):
        self.store = InMemoryGraphStore()
        self.builder = KnowledgeGraphBuilder(self.store)
        self.relationship_engine = RelationshipEngine(self.store)
        self.cache = GraphCache()
        self.search_engine = GraphSearchEngine(self.store, self.relationship_engine, self.cache)
        
        # Build graph on startup
        self.builder.build_from_catalog(movies_db)
        
    def expand_query_entities(self, query: str) -> List[str]:
        """Phase 3: Expands the query using graph relationships."""
        # A simple keyword match to graph nodes could go here
        # E.g. If "Christopher Nolan" is in query, add "Sci-Fi", "Time"
        # For prototype, we'll keep it simple: return an empty list or mock expansion.
        return []
        
    def get_similar_candidates(self, content_ids: List[int], limit: int = 5) -> List[Dict[str, Any]]:
        """Phase 4: Finds structurally similar movies to use as candidates."""
        candidates = []
        seen = set(content_ids)
        
        for c_id in content_ids:
            related_m_ids = self.search_engine.find_related_movies(f"movie:{c_id}", limit=3)
            for rm in related_m_ids:
                try:
                    int_id = int(rm.split(":")[1])
                    if int_id not in seen:
                        seen.add(int_id)
                        candidates.append({"content_id": int_id, "score": 0.8})
                        if len(candidates) >= limit:
                            return candidates
                except Exception:
                    continue
        return candidates
        
    def get_relationship_features(self, content_id_1: int, content_id_2: int) -> Dict[str, float]:
        """Phase 5: Returns graph signals for feature vectors."""
        m1 = f"movie:{content_id_1}"
        m2 = f"movie:{content_id_2}"
        
        rels = self.relationship_engine.infer_movie_relationships(m1, m2)
        
        features = {
            "graph_similarity": self.search_engine.get_graph_similarity(content_id_1, content_id_2),
            "shared_theme_score": 0.0,
            "shared_actor_score": 0.0,
            "shared_director_score": 0.0
        }
        
        for edge_type, weight in rels:
            if edge_type == EdgeType.SHARED_THEME:
                features["shared_theme_score"] = weight
            elif edge_type == EdgeType.SHARED_ACTOR:
                features["shared_actor_score"] = weight
            elif edge_type == EdgeType.SHARED_DIRECTOR:
                features["shared_director_score"] = weight
                
        return features
        
    def get_explanation_context(self, content_id_1: int, content_id_2: int) -> str:
        """Phase 6: Returns deterministic explanations of relationships."""
        m1 = f"movie:{content_id_1}"
        m2 = f"movie:{content_id_2}"
        
        themes = self.search_engine.find_shared_themes(m1, m2)
        directors = self.search_engine.find_shared_directors(m1, m2)
        
        explanations = []
        if directors:
            explanations.append(f"Directed by {', '.join(directors)}")
        if themes:
            explanations.append(f"Explore {', '.join(themes)}")
            
        if not explanations:
            return ""
        return " Both " + " and ".join(explanations) + "."
        
    def get_graph_statistics(self) -> Dict[str, Any]:
        diag = self.store.get_diagnostics()
        return diag.model_dump()
