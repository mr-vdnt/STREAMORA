from typing import Dict, Any, List

class ResponsePlanner:
    """Decides the response strategy, builds the render plan, and manages actions."""
    
    def __init__(self, max_recommendations_in_text: int = 3):
        self.max_recommendations_in_text = max_recommendations_in_text
        
    def plan(self, query: str, intent: str, ui_response_data: List[Dict[str, Any]], profile: str = "concise") -> Dict[str, Any]:
        """
        Determines the strategy and builds the Render Plan.
        Strategy can be:
        - 'deterministic': No LLM needed, use a hardcoded template.
        - 'llm': Use the LLM to generate a conversational response.
        """
        num_results = len(ui_response_data)
        
        # Strategy selection
        if num_results == 0:
            strategy = "deterministic"
            response_type = "no_results"
            intro = "I couldn't find anything matching that in our current catalog."
            actions = [{"type": "refine", "label": "Try a broader search"}]
        elif num_results == 1:
            strategy = "deterministic"
            response_type = "single_recommendation"
            intro = f"I found the perfect match: {ui_response_data[0]['title']}!"
            actions = [
                {"type": "show_more", "label": "Show Similar"},
                {"type": "explain", "label": "Why This Recommendation?"}
            ]
        else:
            strategy = "llm"
            response_type = "multiple_recommendations"
            intro = "Based on your search, here are some excellent choices."
            actions = [
                {"type": "show_more", "label": "Show More Like This"},
                {"type": "explain", "label": "Why These Recommendations?"},
                {"type": "refine", "label": "Filter Results"}
            ]
            
        # Build items for LLM or UI text
        items_for_text = []
        for i in range(min(num_results, self.max_recommendations_in_text)):
            item = ui_response_data[i]
            # Strip out the "Reason: " and scores for the LLM
            # The explanation field looks like "Reason: <reasons> (Score: X, Confidence: Y)"
            raw_expl = item["explanation"]
            if " (Score:" in raw_expl:
                reasons = raw_expl.replace("Reason: ", "").split(" (Score:")[0]
            else:
                reasons = raw_expl
            
            items_for_text.append({
                "title": item["title"],
                "explanations": reasons.split(", ")
            })
            
        render_plan = {
            "strategy": strategy,
            "response_type": response_type,
            "intro": intro,
            "items": items_for_text,
            "actions": actions,
            "profile": profile
        }
        
        return render_plan
