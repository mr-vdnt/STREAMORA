from __future__ import annotations
from typing import List, Optional
from services.recommendation.dtos import RecommendationCandidateDTO, UserIntelligenceProfileDTO

class RecommendationExplainer:
    """
    Layer 9 Structured Evidence Recommendation Explainability Generator.
    Generates transparent recommendation rationale (*"Because you searched for 'Inception'", "Match score: 94%"*).
    """

    def generate_explanation(
        self, 
        candidate: RecommendationCandidateDTO, 
        profile: UserIntelligenceProfileDTO
    ) -> str:
        sources = candidate.provenance_metadata.get("sources", [])

        if "continue_watching" in sources:
            return "Resume watching where you left off"
        elif "search_behavioral" in sources:
            query = candidate.provenance_metadata.get("search_query", "")
            return f"Because you recently searched for '{query}'" if query else "Based on your recent search history"
        elif "knowledge_graph" in sources:
            rel = candidate.provenance_metadata.get("relationship", "related content")
            return f"Connected via {rel} relationship"
        elif "content_based" in sources:
            facts = candidate.provenance_metadata.get("matched_facts", [])
            fact_str = ", ".join(facts[:2]) if facts else "themes"
            return f"Matches your interest in {fact_str}"
        elif "collaborative" in sources:
            return "Top pick amongst users with similar viewing patterns"
        elif "trending" in sources:
            return "Trending across Streamora right now"
        elif "fresh_release" in sources:
            return "Newly released on Streamora"
        else:
            return f"Recommended for you ({int(candidate.score * 100)}% match)"
