from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from services.knowledge.dtos import KnowledgeFactDTO, KnowledgeAssertionDTO

class BaseInferenceEngine(ABC):
    """Abstract Base Class that every Knowledge Inference Engine must implement."""

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Unique identifier for this inference engine."""
        ...

    @property
    @abstractmethod
    def model_version(self) -> str:
        """Version string of the inference engine/model."""
        ...

    @abstractmethod
    async def infer(
        self, 
        content_id: int, 
        content_data: Dict[str, Any], 
        existing_facts: List[KnowledgeFactDTO]
    ) -> List[KnowledgeFactDTO]:
        """Produce new atomic KnowledgeFacts from content metadata and existing facts."""
        ...
