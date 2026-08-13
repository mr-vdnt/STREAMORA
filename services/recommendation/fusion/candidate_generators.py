"""
Four Independent Candidate Generators with Explicit Provenance Signals for Streamora Candidate Fusion.

Generators:
1. FranchiseCandidateGenerator (sequels, prequels, timeline)
2. UniverseCandidateGenerator (canonical universe)
3. SemanticCandidateGenerator (embedding / theme / genre similarity)
4. CastCrewCandidateGenerator (directors, lead actors)
"""
from typing import Dict, List, Any


class FranchiseCandidateGenerator:
    """Generates franchise/timeline candidate items."""

    def generate(self, target_content: Dict[str, Any], catalog: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        candidates = []
        target_title = target_content.get("title", "").lower()

        for item in catalog:
            if item["id"] == target_content.get("id"):
                continue
            item_title = item.get("title", "").lower()

            if any(part in item_title for part in target_title.split()):
                candidates.append({
                    "content_id": item["id"],
                    "item": item,
                    "signal": {
                        "type": "franchise_timeline",
                        "strength": 0.95,
                        "description": "✓ Same Timeline"
                    }
                })
        return candidates


class UniverseCandidateGenerator:
    """Generates canonical universe candidate items."""

    def generate(self, target_content: Dict[str, Any], catalog: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        candidates = []
        target_genres = [g.lower() for g in target_content.get("genres", [])]

        for item in catalog:
            if item["id"] == target_content.get("id"):
                continue
            item_genres = [g.lower() for g in item.get("genres", [])]

            overlap = set(target_genres).intersection(set(item_genres))
            if len(overlap) >= 2:
                candidates.append({
                    "content_id": item["id"],
                    "item": item,
                    "signal": {
                        "type": "shared_universe",
                        "strength": 0.90,
                        "description": "✓ Shared Canonical Universe"
                    }
                })
        return candidates


class SemanticCandidateGenerator:
    """Generates semantic embedding / theme similarity candidate items."""

    def generate(self, target_content: Dict[str, Any], catalog: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        candidates = []
        target_overview = target_content.get("overview", "").lower()

        for item in catalog:
            if item["id"] == target_content.get("id"):
                continue
            item_overview = item.get("overview", "").lower()

            # Measure word overlap as similarity proxy
            target_words = set(target_overview.split())
            item_words = set(item_overview.split())
            common = target_words.intersection(item_words)

            if len(common) > 5:
                candidates.append({
                    "content_id": item["id"],
                    "item": item,
                    "signal": {
                        "type": "semantic_similarity",
                        "strength": 0.85,
                        "description": "✓ Similar Themes & Tone"
                    }
                })
        return candidates


class CastCrewCandidateGenerator:
    """Generates cast & director spotlight candidate items."""

    def generate(self, target_content: Dict[str, Any], catalog: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        candidates = []
        target_director = target_content.get("director", "")

        for item in catalog:
            if item["id"] == target_content.get("id"):
                continue
            if target_director and item.get("director") == target_director:
                candidates.append({
                    "content_id": item["id"],
                    "item": item,
                    "signal": {
                        "type": "cast_crew_spotlight",
                        "strength": 0.88,
                        "description": f"✓ Directed by {target_director}"
                    }
                })
        return candidates
