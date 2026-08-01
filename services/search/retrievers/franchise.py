from __future__ import annotations
from typing import List
from services.search.retrievers.base import BaseRetriever
from services.search.dtos import SearchPlanDTO, RetrievedCandidateDTO
from services.repository.catalog_db import CatalogRepository, FranchiseUniverse, FranchiseMember

class FranchiseRetriever(BaseRetriever):
    """
    Retriever for franchise universe clusters and timelines.
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    @property
    def name(self) -> str:
        return "franchise"

    def supports(self, plan: SearchPlanDTO) -> bool:
        return plan.intent == "franchise_query" or bool(plan.extracted_entities.get("franchises"))

    def estimate_cost(self) -> float:
        return 1.2

    def estimate_recall(self) -> float:
        return 0.95

    async def search(self, plan: SearchPlanDTO) -> List[RetrievedCandidateDTO]:
        candidates: List[RetrievedCandidateDTO] = []
        franchises_extracted = [f.lower() for f in plan.extracted_entities.get("franchises", [])]

        with self.repo.get_session() as session:
            universes = session.query(FranchiseUniverse).all()
            for u in universes:
                if any(fe in str(u.name).lower() or fe in str(u.slug).lower() for fe in franchises_extracted):
                    members = session.query(FranchiseMember).filter(FranchiseMember.franchise_id == u.id).all()
                    for m in members:
                        candidates.append(RetrievedCandidateDTO(
                            content_id=m.content_id,
                            retriever_name=self.name,
                            score=0.90,
                            retrieval_reason=f"Franchise universe member of '{u.name}' (Era: {m.timeline_era or 'Default'})",
                            provenance_metadata={"franchise_name": u.name, "chronological_order": m.chronological_order}
                        ))
        return candidates
