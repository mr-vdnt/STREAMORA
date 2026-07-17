from typing import Dict, Any

class ResponseValidator:
    """Validates the LLM response to ensure it didn't hallucinate or override the recommendation logic."""
    
    def validate(self, llm_response: str, render_plan: Dict[str, Any]) -> bool:
        """
        Validates the text.
        Returns True if valid, False if it detects hallucination.
        """
        if not llm_response:
            return False
            
        # 1. Check for hallucinated movies
        # The LLM should only mention movies that are in the render_plan.
        # This is a basic check: if it contains titles not in the plan, it might be hallucinating.
        # However, a robust check is hard without an NER model. 
        # For our purposes, we will ensure that it AT LEAST mentions the titles it was given.
        
        valid_titles = [item["title"].lower() for item in render_plan.get("items", [])]
        
        # If there are items, make sure at least one is mentioned.
        # If it doesn't mention any, it's a bad response.
        if valid_titles:
            mentioned = False
            llm_lower = llm_response.lower()
            for title in valid_titles:
                if title in llm_lower:
                    mentioned = True
                    break
            if not mentioned:
                return False
                
        # 2. Could add checks for hallucinated directors or genres here.
        
        return True
