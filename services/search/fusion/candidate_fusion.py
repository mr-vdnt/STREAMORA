from __future__ import annotations
from typing import Dict, List
from services.search.dtos import RetrievedCandidateDTO

class CandidateFusionEngine:
    """
    Layer 4 Strategy-Aware Candidate Fusion with Source Provenance Tracking.
    Merges candidates across retrievers, normalizes scores, deduplicates, and preserves provenance.
    """

    RETRIEVER_WEIGHTS = {
        "lexical": 1.0,
        "knowledge_fact": 0.85,
        "relationship": 0.80,
        "franchise": 0.90,
        "embedding": 0.75
    }

    def fuse_candidates(self, raw_candidates: List[RetrievedCandidateDTO]) -> List[RetrievedCandidateDTO]:
        fused_map: Dict[int, RetrievedCandidateDTO] = {}

        for c in raw_candidates:
            cid = c.content_id
            weight = self.RETRIEVER_WEIGHTS.get(c.retriever_name, 0.7)
            weighted_score = c.score * weight

            if cid not in fused_map:
                fused_map[cid] = RetrievedCandidateDTO(
                    content_id=cid,
                    retriever_name=c.retriever_name,
                    score=weighted_score,
                    retrieval_reason=c.retrieval_reason,
                    provenance_metadata={
                        "sources": [c.retriever_name],
                        "source_reasons": [c.retrieval_reason],
                        "source_scores": {c.retriever_name: round(weighted_score, 3)}
                    }
                )
            else:
                existing = fused_map[cid]
                # Accumulate multi-retriever boost
                existing.score = min(1.0, existing.score + (weighted_score * 0.4))
                prov = existing.provenance_metadata
                if c.retriever_name not in prov["sources"]:
                    prov["sources"].append(c.retriever_name)
                    prov["source_reasons"].append(c.retrieval_reason)
                    prov["source_scores"][c.retriever_name] = round(weighted_score, 3)

        sorted_candidates = sorted(fused_map.values(), key=lambda x: x.score, reverse=True)
        return sorted_candidates
