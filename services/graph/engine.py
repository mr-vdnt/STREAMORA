"""
AURORA AI - Knowledge Graph Engine

Abstract interface for graph operations, allowing us to swap
the underlying database (e.g., from NetworkX to Neo4j) in the future.
"""

from abc import ABC, abstractmethod
import pandas as pd
import networkx as nx
import os

class KnowledgeGraph(ABC):
    @abstractmethod
    def build_graph(self):
        pass
        
    @abstractmethod
    def find_path(self, start_node, end_node, max_depth=3) -> list[str]:
        """Finds a readable path between two nodes."""
        pass


class NetworkXGraphEngine(KnowledgeGraph):
    def __init__(self):
        self.G = nx.Graph()
        self.built = False
        
    def build_graph(self):
        print("Building Knowledge Graph...")
        movies_path = "data/raw/movies.csv"
        actors_path = "data/graph/actors.csv"
        directors_path = "data/graph/directors.csv"
        ma_path = "data/graph/movie_actors.csv"
        md_path = "data/graph/movie_directors.csv"
        
        if not os.path.exists(movies_path) or not os.path.exists(actors_path):
            print("Graph data missing. Run enrich_graph_data.py first.")
            return

        movies = pd.read_csv(movies_path)
        actors = pd.read_csv(actors_path)
        directors = pd.read_csv(directors_path)
        movie_actors = pd.read_csv(ma_path)
        movie_directors = pd.read_csv(md_path)
        
        # Add Nodes
        for _, row in movies.iterrows():
            m_id = f"Movie:{row['item_id']}"
            self.G.add_node(m_id, label="Movie", name=row['title'])
            
            # Add Genres
            if pd.notna(row.get('genres')):
                for genre in row['genres'].split('|'):
                    g_id = f"Genre:{genre}"
                    self.G.add_node(g_id, label="Genre", name=genre)
                    self.G.add_edge(m_id, g_id, type="HAS_GENRE")
                    
        for _, row in actors.iterrows():
            a_id = f"Actor:{row['actor_id']}"
            self.G.add_node(a_id, label="Actor", name=row['name'])
            
        for _, row in directors.iterrows():
            d_id = f"Director:{row['director_id']}"
            self.G.add_node(d_id, label="Director", name=row['name'])
            
        # Add Edges
        for _, row in movie_actors.iterrows():
            self.G.add_edge(f"Movie:{row['movie_id']}", f"Actor:{row['actor_id']}", type="ACTS_IN")
            
        for _, row in movie_directors.iterrows():
            self.G.add_edge(f"Movie:{row['movie_id']}", f"Director:{row['director_id']}", type="DIRECTED")
            
        self.built = True
        print(f"Graph built with {self.G.number_of_nodes()} nodes and {self.G.number_of_edges()} edges.")
        
    def find_path(self, start_node, end_node, max_depth=3) -> list[str]:
        if not self.built:
            self.build_graph()
            
        if start_node not in self.G or end_node not in self.G:
            return []
            
        try:
            # Find shortest path
            path = nx.shortest_path(self.G, source=start_node, target=end_node)
            if len(path) - 1 > max_depth:
                return []
                
            # Construct human readable path string
            readable_path = []
            for i in range(len(path) - 1):
                n1 = path[i]
                n2 = path[i+1]
                edge_data = self.G.get_edge_data(n1, n2)
                rel_type = edge_data.get('type', 'RELATED_TO')
                name1 = self.G.nodes[n1].get('name', n1)
                name2 = self.G.nodes[n2].get('name', n2)
                readable_path.append(f"[{name1}] -({rel_type})-> [{name2}]")
                
            return readable_path
        except nx.NetworkXNoPath:
            return []

# Singleton instance
graph_engine = NetworkXGraphEngine()
