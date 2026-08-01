from __future__ import annotations
from typing import List
from services.search.dtos import (
    SearchPlanDTO, RetrievedCandidateDTO, RankingFeatureVectorDTO, ExplanationNodeDTO
)

class SearchExplainabilityGenerator:
    """
    Layer 6 Structured Evidence Search Explainability Generator.
    Generates explicit, structured ExplanationNodeDTO instances for every search result.
    """

    def generate_explanations(
        self, 
        candidate: RetrievedCandidateDTO, 
        fv: RankingFeatureVectorDTO, 
        plan: SearchPlanDTO
    ) -> List[ExplanationNodeDTO]:
        nodes: List[ExplanationNodeDTO] = []
        sources = candidate.provenance_metadata.get("sources", [])

        if "lexical" in sources:
            nodes.append(ExplanationNodeDTO(
                source="Lexical",
                feature="Title/Alias Match",
                score=round(fv.lexical_score, 2),
                weight=0.40,
                description=f"Matched query term '{plan.rewritten_query}' in title/alias index"
            ))

        if "knowledge_fact" in sources:
            facts = candidate.provenance_metadata.get("matched_facts", [])
            fact_str = ", ".join(facts[:2]) if facts else "themes"
            nodes.append(ExplanationNodeDTO(
                source="Knowledge",
                feature=f"Knowledge Fact: {fact_str}",
                score=round(fv.knowledge_overlap_score, 2),
                weight=0.30,
                description=f"Matched active knowledge facts: {fact_str}"
            ))

        if "relationship" in sources:
            rel_type = candidate.provenance_metadata.get("relationship_type", "related")
            nodes.append(ExplanationNodeDTO(
                source="Relationship",
                feature=f"Connected Content ({rel_type})",
                score=0.85,
                weight=0.15,
                description=f"Connected via semantic {rel_type} relationship"
            ))

        if "franchise" in sources:
            fname = candidate.provenance_metadata.get("franchise_name", "Franchise Universe")
            nodes.append(ExplanationNodeDTO(
                source="Franchise",
                feature=f"Universe: {fname}",
                score=0.90,
                weight=0.15,
                description=f"Part of the {fname} timeline"
            ))

        if fv.popularity_score > 0.5:
            nodes.append(ExplanationNodeDTO(
                source="Popularity",
                feature="Global Popularity Boost",
                score=round(fv.popularity_score, 2),
                weight=0.15,
                description=f"Top-tier popularity score ({fv.popularity_score:.2f})"
            ))

        return nodes
