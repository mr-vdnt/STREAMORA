from __future__ import annotations
from typing import List
from services.search.retrievers.base import BaseRetriever
from services.search.dtos import SearchPlanDTO, RetrievedCandidateDTO
from services.repository.catalog_db import CatalogRepository, KnowledgeFact

class KnowledgeFactRetriever(BaseRetriever):
    """
    Knowledge Fact Graph Matcher querying active KnowledgeFacts by theme, mood, setting, and topics.
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    @property
    def name(self) -> str:
        return "knowledge_fact"

    def supports(self, plan: SearchPlanDTO) -> bool:
        return bool(plan.target_themes or plan.target_moods or plan.intent in ["theme_mood_query", "similarity_query"])

    def estimate_cost(self) -> float:
        return 2.0

    def estimate_recall(self) -> float:
        return 0.90

    async def search(self, plan: SearchPlanDTO) -> List[RetrievedCandidateDTO]:
        candidates: List[RetrievedCandidateDTO] = []
        target_values = set(plan.target_themes + plan.target_moods)
        query_words = plan.rewritten_query.lower().split()

        with self.repo.get_session() as session:
            facts = session.query(KnowledgeFact).filter(KnowledgeFact.state == "ACTIVE").all()
            content_scores = {}

            for f in facts:
                val = str(f.value).lower().replace("genre-", "").replace("-", " ")
                overlap_score = 0.0

                if any(t in val for t in target_values):
                    overlap_score += 0.8 * f.confidence * f.source_weight
                elif any(qw in val for qw in query_words):
                    overlap_score += 0.5 * f.confidence * f.source_weight

                if overlap_score > 0.0:
                    cid = f.content_id
                    if cid not in content_scores:
                        content_scores[cid] = {"score": 0.0, "facts": []}
                    content_scores[cid]["score"] += overlap_score
                    content_scores[cid]["facts"].append(f.value)

            for cid, data in content_scores.items():
                normalized_score = min(1.0, data["score"])
                candidates.append(RetrievedCandidateDTO(
                    content_id=cid,
                    retriever_name=self.name,
                    score=normalized_score,
                    retrieval_reason=f"Knowledge fact match on: {', '.join(data['facts'][:3])}",
                    provenance_metadata={"matched_facts": data["facts"]}
                ))

        return candidates
