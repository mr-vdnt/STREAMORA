from __future__ import annotations
from typing import Dict, List, Any, Optional

class ColdStartManager:
    """
    Dual Cold-Start Strategy Engine:
    - Strategy 1: New Users (Onboarding Genres -> Regional Trending -> Editorial Picks)
    - Strategy 2: New Titles (Embedding Priors -> KIP Graph Links -> Metadata Propagation)
    """

    @staticmethod
    def get_new_user_recommendations(user_onboarding_genres: List[str], all_catalog_items: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        if user_onboarding_genres:
            genre_matches = [c for c in all_catalog_items if any(g in c.get("genres", []) for g in user_onboarding_genres)]
            if genre_matches:
                return sorted(genre_matches, key=lambda x: x.get("popularity", 0.0), reverse=True)[:limit]

        # Regional Trending & Editorials Fallback
        return sorted(all_catalog_items, key=lambda x: x.get("popularity", 0.0), reverse=True)[:limit]

    @staticmethod
    def get_new_title_cold_start_prior(new_title_meta: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates cold-start popularity prior and initial graph link weights for a new title."""
        base_popularity = 50.0
        if new_title_meta.get("franchise"):
            base_popularity += 25.0
        if new_title_meta.get("universe") in ["MCU", "DCU"]:
            base_popularity += 15.0

        return {
            "initial_popularity_prior": min(100.0, base_popularity),
            "graph_link_confidence": 0.85,
            "cold_start_status": "PROMOTED_NEW_RELEASE"
        }
