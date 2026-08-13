"""
Multi-Signal Candidate Fusion Engine & Weighted LTR Ranker for Streamora V3.1.

Features:
- Fuses candidates from 4 independent generators (Franchise, Universe, Semantic, Cast/Crew).
- Applies User Preference Vector affinity scoring.
- Enforces 80/20 Exploitation vs Exploration split for serendipity.
- Attaches explicit, human-readable rationale nodes to output items.
"""
import random
from typing import Dict, List, Any
from services.recommendation.fusion.candidate_generators import (
    FranchiseCandidateGenerator,
    UniverseCandidateGenerator,
    SemanticCandidateGenerator,
    CastCrewCandidateGenerator,
    TrendingCandidateGenerator,
    ContentCandidateGenerator
)
from services.recommendation.collaborative_filtering import CollaborativeCandidateGenerator


class CandidateFusionEngine:
    """Fuses multi-signal candidates across 7 generators and applies weighted LTR ranking with exploration."""

    def __init__(self):
        self.franchise_gen = FranchiseCandidateGenerator()
        self.universe_gen = UniverseCandidateGenerator()
        self.semantic_gen = SemanticCandidateGenerator()
        self.cast_crew_gen = CastCrewCandidateGenerator()
        self.trending_gen = TrendingCandidateGenerator()
        self.content_gen = ContentCandidateGenerator()
        self.collaborative_gen = CollaborativeCandidateGenerator()

    def fuse_and_rank(
        self,
        target_content: Dict[str, Any],
        catalog: List[Dict[str, Any]],
        user_preference_vector: Dict[str, float],
        top_k: int = 10,
        user_id: str = "guest_user"
    ) -> List[Dict[str, Any]]:
        # 1. Collect candidates across all 7 generators
        raw_candidates = []
        raw_candidates.extend(self.franchise_gen.generate(target_content, catalog))
        raw_candidates.extend(self.universe_gen.generate(target_content, catalog))
        raw_candidates.extend(self.semantic_gen.generate(target_content, catalog))
        raw_candidates.extend(self.cast_crew_gen.generate(target_content, catalog))
        raw_candidates.extend(self.trending_gen.generate(target_content, catalog))
        raw_candidates.extend(self.content_gen.generate(target_content, catalog))
        
        # Collaborative filtering candidate generator
        collab_items = self.collaborative_gen.generate(user_id, target_content, catalog)
        for c in collab_items:
            raw_candidates.append({
                "content_id": c["candidate_id"],
                "item": c["item"],
                "signal": {
                    "type": "collaborative_filtering",
                    "strength": c["signals"][0]["strength"],
                    "description": c["rationale_hint"]
                }
            })

        # Deduplicate candidates while collecting all signals
        fused_map: Dict[int, Dict[str, Any]] = {}
        for cand in raw_candidates:
            cid = cand["content_id"]
            if cid not in fused_map:
                fused_map[cid] = {
                    "item": cand["item"],
                    "signals": [cand["signal"]],
                    "base_score": cand["signal"]["strength"]
                }
            else:
                fused_map[cid]["signals"].append(cand["signal"])
                fused_map[cid]["base_score"] += cand["signal"]["strength"] * 0.5

        # 2. Score candidates against User Preference Vector
        scored_candidates = []
        for cid, candidate in fused_map.items():
            item = candidate["item"]
            genres = [g.lower() for g in item.get("genres", [])]
            
            # User preference affinity score
            pref_score = sum(user_preference_vector.get(g, 0.50) for g in genres) / max(1, len(genres))
            
            final_score = (candidate["base_score"] * 0.60) + (pref_score * 0.40)
            
            # Primary signal description as rationale node
            primary_rationale = candidate["signals"][0]["description"]
            
            item_copy = item.copy()
            item_copy["rationale"] = primary_rationale
            item_copy["fusion_signals"] = candidate["signals"]
            item_copy["rank_score"] = round(final_score, 4)
            
            scored_candidates.append(item_copy)

        # 3. Sort candidates by final score (Exploitation)
        scored_candidates.sort(key=lambda x: x["rank_score"], reverse=True)

        # 4. Enforce 80/20 Exploitation vs Exploration Split
        exploitation_count = max(1, int(top_k * 0.80)) if top_k > 1 else top_k
        exploration_count = top_k - exploitation_count

        final_slate = scored_candidates[:exploitation_count]
        remaining = scored_candidates[exploitation_count:]

        if remaining:
            exploration_items = random.sample(remaining, min(exploration_count, len(remaining)))
            final_slate.extend(exploration_items)

        # Fallback if catalog candidates are low: fill with remaining catalog items
        if len(final_slate) < top_k:
            seen_ids = {x["id"] for x in final_slate}
            seen_ids.add(target_content.get("id"))
            for item in catalog:
                if item["id"] not in seen_ids:
                    item_copy = item.copy()
                    item_copy["rationale"] = "✓ Recommended for You"
                    final_slate.append(item_copy)
                    if len(final_slate) >= top_k:
                        break

        return final_slate[:top_k]

    def fuse_candidates(self, raw_candidates: List[Any]) -> List[Any]:
        """Method alias for recommendation pipeline candidate fusion with content_id deduplication and provenance metadata."""
        if not raw_candidates:
            return []
        fused_map: Dict[Any, Any] = {}
        for cand in raw_candidates:
            item = getattr(cand, "item", cand) if not isinstance(cand, dict) else cand.get("item", cand)
            cid = getattr(item, "content_id", None) if not isinstance(item, dict) else item.get("content_id", item.get("id"))
            gen_name = getattr(cand, "generator_name", "unknown") if not isinstance(cand, dict) else cand.get("generator_name", "unknown")

            if cid not in fused_map:
                if hasattr(cand, "provenance_metadata") and isinstance(cand.provenance_metadata, dict):
                    cand.provenance_metadata["sources"] = [gen_name]
                elif isinstance(cand, dict):
                    if "provenance_metadata" not in cand:
                        cand["provenance_metadata"] = {}
                    cand["provenance_metadata"]["sources"] = [gen_name]
                fused_map[cid] = cand
            else:
                existing = fused_map[cid]
                if hasattr(existing, "provenance_metadata") and isinstance(existing.provenance_metadata, dict):
                    if "sources" not in existing.provenance_metadata:
                        existing.provenance_metadata["sources"] = []
                    if gen_name not in existing.provenance_metadata["sources"]:
                        existing.provenance_metadata["sources"].append(gen_name)

        return list(fused_map.values())


# Alias for backward compatibility with pre-existing pipeline imports
RecommendationCandidateFuser = CandidateFusionEngine
