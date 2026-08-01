from __future__ import annotations
from typing import Dict, List
from services.recommendation.dtos import RecommendationCandidateDTO

class RecommendationCandidateFuser:
    """
    Layer 4 Strategy-Aware Candidate Fusion with Provenance Tracking.
    Merges candidate streams across generators, normalizes scores, deduplicates, and preserves provenance.
    """

    GENERATOR_WEIGHTS = {
        "continue_watching": 1.0,
        "search_behavioral": 0.95,
        "content_based": 0.90,
        "knowledge_graph": 0.85,
        "collaborative": 0.88,
        "trending": 0.80,
        "fresh_release": 0.82,
        "editorial": 0.85,
        "exploration": 0.70
    }

    def fuse_candidates(self, raw_candidates: List[RecommendationCandidateDTO]) -> List[RecommendationCandidateDTO]:
        fused_map: Dict[int, RecommendationCandidateDTO] = {}

        for c in raw_candidates:
            cid = c.content_id
            weight = self.GENERATOR_WEIGHTS.get(c.generator_name, 0.75)
            weighted_score = c.score * weight

            if cid not in fused_map:
                fused_map[cid] = RecommendationCandidateDTO(
                    content_id=cid,
                    generator_name=c.generator_name,
                    score=weighted_score,
                    reason=c.reason,
                    provenance_metadata={
                        "sources": [c.generator_name],
                        "reasons": [c.reason],
                        "source_scores": {c.generator_name: round(weighted_score, 3)}
                    }
                )
            else:
                existing = fused_map[cid]
                existing.score = min(1.0, existing.score + (weighted_score * 0.3))
                prov = existing.provenance_metadata
                if c.generator_name not in prov["sources"]:
                    prov["sources"].append(c.generator_name)
                    prov["reasons"].append(c.reason)
                    prov["source_scores"][c.generator_name] = round(weighted_score, 3)

        sorted_candidates = sorted(fused_map.values(), key=lambda x: x.score, reverse=True)
        return sorted_candidates
