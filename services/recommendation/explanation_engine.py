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
        explanations = []
        
        # 1. Similarity to seed
        sim = float(context.get('similarity', 0.0))
        if sim > 0.8:
            explanations.append("Similar themes and pacing")
            
        # 2. High rating
        rating = float(item.get('rating', 0) or 0)
        if rating >= 8.5:
            explanations.append("Critically acclaimed")
            
        # 3. Popularity
        pop = float(item.get('popularity', 0) or 0)
        if pop > 80:
            explanations.append("Trending worldwide")
            
        # 4. Indian Content
        lang = str(item.get('language', '')).lower()
        if lang in ['hi', 'ta', 'te', 'ml', 'kn', 'bn']:
            explanations.append("Top regional pick")
            
        # 5. Same Director
        if float(context.get('same_director', 0.0)) > 0:
            dir_name = item.get('director', 'this director')
            explanations.append(f"Directed by {dir_name}")
            
        # 6. Fallback
        if not explanations:
            explanations.append("Recommended for you")
            
        return explanations

    def generate_detailed_explanation(self, item: dict, seed_item: Optional[dict] = None) -> dict:
        rating = float(item.get('rating', 8.0) or 8.0)
        match_score = min(99, int(rating * 10) + 5)
        
        seed_title = seed_item.get("title", "Interstellar") if seed_item else "Interstellar"
        genres = item.get("genres", ["Sci-Fi", "Drama"])
        if isinstance(genres, str):
            genres = [g.strip() for g in genres.split("|") if g.strip()]

        return {
            "reason": f"Because you watched {seed_title}",
            "match_score": match_score,
            "similarity_percentage": match_score,
            "shared_themes": genres[:4] if genres else ["Cinematic", "Drama", "Storytelling"]
        }

