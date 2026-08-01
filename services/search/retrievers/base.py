from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
from services.search.dtos import SearchPlanDTO, RetrievedCandidateDTO

class BaseRetriever(ABC):
    """Abstract Base Class for pluggable retrieval strategies in the Retrieval Marketplace."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this retriever."""
        ...

    @abstractmethod
    def supports(self, plan: SearchPlanDTO) -> bool:
        """Check if this retriever supports the given SearchPlan."""
        ...

    @abstractmethod
    def estimate_cost(self) -> float:
        """Estimate relative computation cost (0.1 to 10.0)."""
        ...

    @abstractmethod
    def estimate_recall(self) -> float:
        """Estimate expected recall (0.0 to 1.0)."""
        ...

    @abstractmethod
    async def search(self, plan: SearchPlanDTO) -> List[RetrievedCandidateDTO]:
        """Execute candidate retrieval given a SearchPlan."""
        ...
