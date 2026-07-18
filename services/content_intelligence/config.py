# Configuration for the Content Intelligence Knowledge Graph

GRAPH_CONFIG = {
    "max_graph_depth": 3,
    "similarity_threshold": 0.5,
    "traversal_limit": 100,
    "neighbor_limit": 20,
    
    # Edge Weights
    "edge_weights": {
        "DIRECTED_BY": 1.0,
        "ACTED_IN": 0.5,
        "HAS_GENRE": 0.3,
        "HAS_THEME": 0.6,
        "HAS_KEYWORD": 0.4,
        "SIMILAR_TO": 0.8,
        "SHARED_DIRECTOR": 0.9,
        "SHARED_ACTOR": 0.4,
        "SHARED_THEME": 0.5
    }
}
