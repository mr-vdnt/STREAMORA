from __future__ import annotations
from typing import List
from services.search.retrievers.base import BaseRetriever
from services.search.dtos import SearchPlanDTO, RetrievedCandidateDTO
from services.repository.catalog_db import CatalogRepository, SearchDocument, Content

class LexicalRetriever(BaseRetriever):
    """
    Lexical BM25 / Fuzzy Title & Keyword Retriever.
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    @property
    def name(self) -> str:
        return "lexical"

    def supports(self, plan: SearchPlanDTO) -> bool:
        return True

    def estimate_cost(self) -> float:
        return 1.0

    def estimate_recall(self) -> float:
        return 0.85

    async def search(self, plan: SearchPlanDTO) -> List[RetrievedCandidateDTO]:
        candidates: List[RetrievedCandidateDTO] = []
        q = plan.rewritten_query.lower().strip()

        with self.repo.get_session() as session:
            # Query SearchDocument & Content
            docs = session.query(SearchDocument).all()
            for d in docs:
                score = 0.0
                norm_title = str(d.normalized_title or "").lower()
                if q == norm_title:
                    score = 1.0
                elif q in norm_title or norm_title in q:
                    score = 0.8
                elif d.aliases and q in str(d.aliases).lower():
                    score = 0.75
                elif d.keywords and q in str(d.keywords).lower():
                    score = 0.6

                if score > 0.0:
                    candidates.append(RetrievedCandidateDTO(
                        content_id=d.content_id,
                        retriever_name=self.name,
                        score=score,
                        retrieval_reason=f"Lexical match on title '{norm_title}'",
                        provenance_metadata={"matched_term": q, "title": norm_title}
                    ))

        return candidates
