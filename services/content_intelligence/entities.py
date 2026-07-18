from typing import Dict, Any, List
from .models import GraphNode, NodeType
import re

class EntityExtractionEngine:
    """Extracts structured graph entities from raw movie metadata."""
    
    def extract_entities(self, content_id: int, movie: Dict[str, Any]) -> List[GraphNode]:
        entities = []
        
        # 1. Movie Node itself
        title = movie.get("title", f"Movie {content_id}")
        movie_node = GraphNode(
            id=f"movie:{content_id}",
            type=NodeType.MOVIE,
            name=title,
            metadata={"year": str(movie.get("year", ""))}
        )
        entities.append(movie_node)
        
        # 2. Director Nodes
        director_str = movie.get("director", "")
        if director_str:
            for d in director_str.split(", "):
                d = d.strip()
                if d:
                    d_id = self._normalize_id(d)
                    entities.append(GraphNode(id=f"director:{d_id}", type=NodeType.DIRECTOR, name=d))
                    
        # 3. Actor Nodes
        actor_str = movie.get("cast", "")
        if actor_str:
            for a in actor_str.split(", "):
                a = a.strip()
                if a:
                    a_id = self._normalize_id(a)
                    entities.append(GraphNode(id=f"actor:{a_id}", type=NodeType.ACTOR, name=a))
                    
        # 4. Genre Nodes
        genre_str = movie.get("genres", "")
        if genre_str:
            for g in genre_str.split("|"):
                g = g.strip()
                if g:
                    g_id = self._normalize_id(g)
                    entities.append(GraphNode(id=f"genre:{g_id}", type=NodeType.GENRE, name=g))
                    
        # 5. Theme Nodes (if available)
        theme_str = movie.get("themes", "")
        if theme_str:
            for t in theme_str.split(","):
                t = t.strip()
                if t:
                    t_id = self._normalize_id(t)
                    entities.append(GraphNode(id=f"theme:{t_id}", type=NodeType.THEME, name=t))
                    
        return entities
        
    def _normalize_id(self, text: str) -> str:
        """Converts 'Christopher Nolan' to 'christopher_nolan'"""
        text = text.lower().strip()
        text = re.sub(r'[^a-z0-9]+', '_', text)
        return text.strip('_')
