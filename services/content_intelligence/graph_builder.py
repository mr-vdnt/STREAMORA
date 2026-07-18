from typing import Dict, Any
from .graph_store import GraphStore
from .entities import EntityExtractionEngine
from .models import GraphEdge, EdgeType, NodeType
from .config import GRAPH_CONFIG

class KnowledgeGraphBuilder:
    """Constructs the Knowledge Graph from the movie catalog."""
    
    def __init__(self, store: GraphStore):
        self.store = store
        self.extractor = EntityExtractionEngine()
        
    def build_from_catalog(self, movies_db: Dict[int, Any]) -> None:
        weights = GRAPH_CONFIG["edge_weights"]
        
        # Phase 1: Add all nodes and primary edges
        for content_id, movie in movies_db.items():
            entities = self.extractor.extract_entities(content_id, movie)
            
            # Find the movie node
            movie_node = next((e for e in entities if e.type == NodeType.MOVIE), None)
            if not movie_node:
                continue
                
            # Add all extracted nodes
            for entity in entities:
                self.store.add_node(entity)
                
            # Add edges between movie and its attributes
            for entity in entities:
                if entity.type == NodeType.MOVIE:
                    continue
                    
                edge_type = None
                weight = 1.0
                
                if entity.type == NodeType.DIRECTOR:
                    edge_type = EdgeType.DIRECTED_BY
                elif entity.type == NodeType.ACTOR:
                    edge_type = EdgeType.ACTED_IN
                elif entity.type == NodeType.GENRE:
                    edge_type = EdgeType.HAS_GENRE
                elif entity.type == NodeType.THEME:
                    edge_type = EdgeType.HAS_THEME
                    
                if edge_type:
                    weight = weights.get(edge_type.value, 1.0)
                    
                    # Add directed edge from Movie -> Attribute
                    self.store.add_edge(GraphEdge(
                        source_id=movie_node.id,
                        target_id=entity.id,
                        type=edge_type,
                        weight=weight
                    ))
                    
                    # Add directed edge from Attribute -> Movie for reverse lookups
                    self.store.add_edge(GraphEdge(
                        source_id=entity.id,
                        target_id=movie_node.id,
                        type=edge_type,
                        weight=weight
                    ))
