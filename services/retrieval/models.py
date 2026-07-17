from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import time

class GeneratorMetadata(BaseModel):
    name: str
    rank: int
    score: float

class RetrievalMetadata(BaseModel):
    generators: List[GeneratorMetadata]
    fusion_score: float = 0.0

class RetrievalContext(BaseModel):
    fingerprint: str
    catalog_version: int = 1
    retrieval_timestamp: float = Field(default_factory=time.time)

class Candidate(BaseModel):
    content_id: int
    retrieval: RetrievalMetadata
    context: RetrievalContext
