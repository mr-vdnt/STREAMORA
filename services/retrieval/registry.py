from typing import List, Type
from .generators.base import CandidateGenerator

class GeneratorRegistry:
    def __init__(self):
        self._generators: List[CandidateGenerator] = []
        
    def register(self, generator: CandidateGenerator):
        self._generators.append(generator)
        
    def get_all(self) -> List[CandidateGenerator]:
        return self._generators
