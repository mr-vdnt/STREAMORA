from __future__ import annotations
from typing import List, Dict, Any
from services.recommendation.contracts import BaseCandidateGenerator
from services.recommendation.dtos import RecommendationPlanDTO, RecommendationCandidateDTO, UserIntelligenceProfileDTO
from services.repository.catalog_db import CatalogRepository, KnowledgeRelationship, FranchiseMember

class RecommendationGraph:
    """
    Traverses User -> Content -> Theme -> Mood -> Actor -> Franchise relationships.
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    def traverse_related_content(self, context_content_id: int) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        with self.repo.get_session() as session:
            rels = session.query(KnowledgeRelationship).filter(
                KnowledgeRelationship.source_content_id == context_content_id
            ).all()

            for r in rels:
                results.append({
                    "target_id": r.target_content_id,
                    "relationship": r.relationship_type,
                    "strength": r.strength
                })
        return results

class KnowledgeGraphCandidateGenerator(BaseCandidateGenerator):
    """
    Knowledge Graph Candidate Generator.
    Traverses franchise timelines, sequels, spin-offs, and thematic twins.
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()
        self.graph = RecommendationGraph(self.repo)

    @property
    def name(self) -> str:
        return "knowledge_graph"

    def supports(self, plan: RecommendationPlanDTO) -> bool:
        return plan.context_item_id is not None or plan.slate_type in ["because_you_watched", "personalized_home"]

    def estimate_cost(self) -> float:
        return 1.8

    async def generate_candidates(
        self, 
        plan: RecommendationPlanDTO, 
        profile: UserIntelligenceProfileDTO
    ) -> List[RecommendationCandidateDTO]:
        candidates: List[RecommendationCandidateDTO] = []
        context_id = plan.context_item_id or 1

        related_nodes = self.graph.traverse_related_content(context_id)
        for node in related_nodes:
            candidates.append(RecommendationCandidateDTO(
                content_id=node["target_id"],
                generator_name=self.name,
                score=0.85 * node["strength"],
                reason=f"Connected via Knowledge Graph ({node['relationship']})",
                provenance_metadata={"relationship": node["relationship"]}
            ))

        return candidates
