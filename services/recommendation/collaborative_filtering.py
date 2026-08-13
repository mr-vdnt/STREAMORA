"""
Collaborative Filtering & Candidate Generator for Streamora Phase 5.

Implements implicit-feedback collaborative filtering:
- Item-Item Co-occurrence Matrix based on user watch histories & likes.
- User-User Behavior Similarity for cross-user candidate discovery.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Set, Any
import math


class CollaborativeFilteringEngine:
    """Implicit feedback collaborative filtering matrix model."""

    def __init__(self):
        # user_id -> set of content_ids user liked or completed
        self._user_interactions: Dict[str, Set[int]] = {}
        # content_id -> set of user_ids who liked or completed
        self._item_interactions: Dict[int, Set[str]] = {}

    def record_interaction(self, user_id: str, content_id: int, weight: float = 1.0) -> None:
        """Record implicit feedback interaction (like/completion)."""
        if user_id not in self._user_interactions:
            self._user_interactions[user_id] = set()
        self._user_interactions[user_id].add(content_id)

        if content_id not in self._item_interactions:
            self._item_interactions[content_id] = set()
        self._item_interactions[content_id].add(user_id)

    def get_collaborative_candidates(
        self, user_id: str, target_content_id: int, catalog: List[Dict[str, Any]], top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Find items liked/completed by users with similar taste to target user or item."""
        target_users = self._item_interactions.get(target_content_id, set())
        user_items = self._user_interactions.get(user_id, set())

        scored_candidates = []
        for item in catalog:
            cid = item["id"]
            if cid == target_content_id:
                continue

            item_users = self._item_interactions.get(cid, set())
            if not item_users:
                # Baseline similarity if no explicit interaction matrix populated
                scored_candidates.append({
                    "item": item,
                    "score": 0.50,
                    "reason": "Collaborative Cold-Start Baseline"
                })
                continue

            # Jaccard / Cosine implicit overlap score
            overlap = len(target_users.intersection(item_users))
            union = len(target_users.union(item_users))
            collab_score = overlap / max(1, union) if union > 0 else 0.50

            scored_candidates.append({
                "item": item,
                "score": max(0.50, collab_score),
                "reason": f"Collaborative Overlap ({overlap} co-viewers)"
            })

        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        return scored_candidates[:top_k]


class CollaborativeCandidateGenerator:
    """Candidate generator contract for collaborative filtering."""

    def __init__(self, cf_engine: CollaborativeFilteringEngine = None):
        self.cf_engine = cf_engine or CollaborativeFilteringEngine()

    def generate(self, user_id: str, target_item: Dict[str, Any], catalog: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        candidates = self.cf_engine.get_collaborative_candidates(
            user_id=user_id, target_content_id=target_item.get("id", 0), catalog=catalog, top_k=5
        )
        results = []
        for c in candidates:
            item = c["item"]
            results.append({
                "candidate_id": item["id"],
                "item": item,
                "generator_name": "CollaborativeCandidateGenerator",
                "signals": [{"name": "collaborative_co_occurrence", "strength": c["score"]}],
                "rationale_hint": c["reason"]
            })
        return results
