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
