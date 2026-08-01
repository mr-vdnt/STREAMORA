from __future__ import annotations
from typing import List
from services.search.retrievers.base import BaseRetriever
from services.search.dtos import SearchPlanDTO, RetrievedCandidateDTO
from services.repository.catalog_db import CatalogRepository, KnowledgeRelationship

class RelationshipRetriever(BaseRetriever):
    """
    Retriever for inter-content relationships (sequels, spin-offs, thematic twins).
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    @property
    def name(self) -> str:
        return "relationship"

    def supports(self, plan: SearchPlanDTO) -> bool:
        return plan.intent in ["similarity_query", "franchise_query"]

    def estimate_cost(self) -> float:
        return 1.5

    def estimate_recall(self) -> float:
        return 0.80

    async def search(self, plan: SearchPlanDTO) -> List[RetrievedCandidateDTO]:
        candidates: List[RetrievedCandidateDTO] = []
        with self.repo.get_session() as session:
            relationships = session.query(KnowledgeRelationship).all()
            for rel in relationships:
                candidates.append(RetrievedCandidateDTO(
                    content_id=rel.target_content_id,
                    retriever_name=self.name,
                    score=0.85 * rel.strength,
                    retrieval_reason=f"Relationship match ({rel.relationship_type}) from content_id {rel.source_content_id}",
                    provenance_metadata={"relationship_type": rel.relationship_type, "source_id": rel.source_content_id}
                ))
        return candidates
