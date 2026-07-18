from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set
from .models import GraphNode, GraphEdge, EdgeType, GraphDiagnostics
import datetime

class GraphStore(ABC):
    @abstractmethod
    def add_node(self, node: GraphNode) -> None:
        pass
        
    @abstractmethod
    def add_edge(self, edge: GraphEdge) -> None:
        pass
        
    @abstractmethod
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        pass
        
    @abstractmethod
    def get_edges(self, node_id: str, edge_type: Optional[EdgeType] = None) -> List[GraphEdge]:
        pass
        
    @abstractmethod
    def node_exists(self, node_id: str) -> bool:
        pass
        
    @abstractmethod
    def get_diagnostics(self) -> GraphDiagnostics:
        pass

class InMemoryGraphStore(GraphStore):
    def __init__(self):
        self._nodes: Dict[str, GraphNode] = {}
        # Adjacency list: node_id -> target_id -> edge
        self._edges: Dict[str, Dict[str, GraphEdge]] = {} 
        self.revision = 1
        self.build_timestamp = datetime.datetime.utcnow().isoformat()
        
    def add_node(self, node: GraphNode) -> None:
        if node.id not in self._nodes:
            self._nodes[node.id] = node
            self._edges[node.id] = {}
            
    def add_edge(self, edge: GraphEdge) -> None:
        # Create nodes implicitly if they don't exist? No, builder should handle it.
        if edge.source_id in self._nodes and edge.target_id in self._nodes:
            # Upsert edge
            self._edges[edge.source_id][edge.target_id] = edge
            # Undirected graphs would add the reverse edge too, but our graph is directed.
            # We can traverse both ways by searching, but for performance we might add reverse edges in builder.
            
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self._nodes.get(node_id)
        
    def get_edges(self, node_id: str, edge_type: Optional[EdgeType] = None) -> List[GraphEdge]:
        if node_id not in self._edges:
            return []
            
        edges = list(self._edges[node_id].values())
        if edge_type:
            edges = [e for e in edges if e.type == edge_type]
        return edges
        
    def get_incoming_edges(self, target_id: str, edge_type: Optional[EdgeType] = None) -> List[GraphEdge]:
        """Utility for traversals that go 'backwards'"""
        incoming = []
        for source_id, targets in self._edges.items():
            if target_id in targets:
                edge = targets[target_id]
                if not edge_type or edge.type == edge_type:
                    incoming.append(edge)
        return incoming
        
    def node_exists(self, node_id: str) -> bool:
        return node_id in self._nodes
        
    def get_diagnostics(self) -> GraphDiagnostics:
        edges_count = sum(len(targets) for targets in self._edges.values())
        return GraphDiagnostics(
            schema_version="1.0",
            graph_revision=self.revision,
            build_timestamp=self.build_timestamp,
            nodes_count=len(self._nodes),
            edges_count=edges_count
        )
