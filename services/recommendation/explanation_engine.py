from typing import Optional, List, Dict, Any

class ExplanationEngine:

    """
    Generates dynamic 'Why we recommend this' text using matched signals.
    """
    def __init__(self):
        pass
        
    def generate_explanation(self, item: dict, context: dict) -> list[str]:
        """
        Takes in the movie payload and ranking context, returns a list of human-readable tags.
        """
        # Obsolete, replacing with detailed explanation
        return []

    def generate_detailed_explanation(self, item: dict, seed_item: Optional[dict] = None) -> dict:
        context = item.get("context", {})
        seed_title = seed_item.get("title", "") if seed_item else ""
        
        reason = None
        reason_type = None
        reason_id = None
        confidence = 0.0
        
        if context.get("same_actor"):
            reason_type = "same_actor"
            actor = context.get("actor_name", "this actor")
            reason = f"Featuring {actor}"
            reason_id = context.get("actor_id")
            confidence = context.get("actor_confidence", 0.9)
        elif context.get("same_director"):
            reason_type = "same_director"
            director = context.get("director_name", "this director")
            reason = f"Directed by {director}"
            reason_id = context.get("director_id")
            confidence = context.get("director_confidence", 0.9)
        elif context.get("same_franchise"):
            reason_type = "same_franchise"
            franchise = context.get("franchise", "same")
            reason = f"Part of the {franchise} universe"
            reason_id = context.get("franchise_id")
            confidence = context.get("franchise_confidence", 0.95)
        elif context.get("genre_similarity"):
            reason_type = "genre_similarity"
            genre = context.get("genre", "similar")
            reason = f"Similar {genre} themes"
            reason_id = context.get("genre_id")
            confidence = context.get("genre_confidence", 0.8)
        elif context.get("semantic_similarity") and seed_title:
            reason_type = "semantic_similarity"
            reason = f"Similar to {seed_title}"
            reason_id = str(seed_item.get("id")) if seed_item else None
            confidence = context.get("semantic_confidence", 0.85)

        return {
            "reason": reason,
            "reason_type": reason_type,
            "reason_id": reason_id,
            "confidence": confidence,
            "reason_text": reason
        }

