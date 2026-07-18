from typing import Dict, Any
from .models import GraphDiagnostics

class DiagnosticsEngine:
    """Helper to collect and format graph diagnostics."""
    
    @staticmethod
    def format_diagnostics(diag: GraphDiagnostics) -> Dict[str, Any]:
        return {
            "nodes": diag.nodes_count,
            "edges": diag.edges_count,
            "graph_version": diag.schema_version,
            "graph_revision": diag.graph_revision,
            "build_timestamp": diag.build_timestamp,
            "adapter_latency_ms": diag.adapter_latency_ms
        }
