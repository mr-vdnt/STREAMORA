class TemplateSelector:
    """Selects the appropriate response template based on the render plan."""
    
    def select_template(self, render_plan: dict) -> dict:
        """
        Returns a dictionary containing the system prompt and instructions for the LLM.
        """
        profile = render_plan.get("profile", "concise")
        
        # Profile adjustments
        length_instruction = "Keep it to 2 sentences."
        tone_instruction = "You are a helpful AI movie curator."
        
        if profile == "detailed":
            length_instruction = "Provide a slightly more detailed explanation of why these match. Keep it to 3 or 4 sentences."
        elif profile == "enthusiastic":
            tone_instruction = "You are an extremely enthusiastic AI movie curator. Use exclamation points and show excitement!"
            
        system_prompt = f"{tone_instruction} The system found multiple great matches for the user's query. Present the TOP movies from the provided list, mentioning their titles and why they match (using the provided reasons). Do NOT invent movies or reasons. {length_instruction}"
        
        return {
            "posture": "curated",
            "system_prompt": system_prompt
        }
