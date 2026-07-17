from abc import ABC, abstractmethod
from typing import List, Dict, Any

class CandidateGenerator(ABC):
    """
    Base class for all retrieval generators.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
        
    @abstractmethod
    def retrieve(self, query_contract: dict) -> List[Dict[str, Any]]:
        """
        Retrieves candidates based on the query contract.
        Returns a list of dicts with at least 'content_id' and 'score'.
        """
        pass
