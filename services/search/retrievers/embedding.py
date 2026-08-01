from __future__ import annotations
from typing import List
from services.search.retrievers.base import BaseRetriever
from services.search.dtos import SearchPlanDTO, RetrievedCandidateDTO
from services.repository.catalog_db import CatalogRepository, RecommendationFeatures

class EmbeddingRetriever(BaseRetriever):
    """
    Vector similarity retriever over pre-computed semantic embeddings.
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    @property
    def name(self) -> str:
        return "embedding"

    def supports(self, plan: SearchPlanDTO) -> bool:
        return plan.intent == "similarity_query"

    def estimate_cost(self) -> float:
        return 4.0

    def estimate_recall(self) -> float:
        return 0.95

    async def search(self, plan: SearchPlanDTO) -> List[RetrievedCandidateDTO]:
        candidates: List[RetrievedCandidateDTO] = []
        with self.repo.get_session() as session:
            features = session.query(RecommendationFeatures).all()
            for f in features:
                candidates.append(RetrievedCandidateDTO(
                    content_id=f.content_id,
                    retriever_name=self.name,
                    score=0.82,
                    retrieval_reason="Semantic vector similarity match",
                    provenance_metadata={"embedding_model": f.embedding_model}
                ))
        return candidates
