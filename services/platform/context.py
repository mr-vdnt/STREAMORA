import time
from typing import Dict, Any, Optional
import uuid

class RequestContext:
    """Unified context that flows through the recommendation pipeline."""
    
    def __init__(self, user_id: str = "anonymous", session_id: Optional[str] = None):
        self.request_id = str(uuid.uuid4())
        self.user_id = user_id
        self.session_id = session_id or str(uuid.uuid4())
        self.start_time = time.perf_counter()
        
        # Diagnostics
        self.diagnostics: Dict[str, Any] = {
            "query_intelligence_ms": 0,
            "hybrid_retrieval_ms": 0,
            "decision_engine_ms": 0,
            "presentation_ms": 0,
            "total_ms": 0
        }
        
    def record_timing(self, stage: str, duration_ms: float):
        self.diagnostics[f"{stage}_ms"] = int(duration_ms)
        
    def finish(self):
        self.diagnostics["total_ms"] = int((time.perf_counter() - self.start_time) * 1000)
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "diagnostics": self.diagnostics
        }
