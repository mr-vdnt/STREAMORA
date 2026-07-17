class TemplateSelector:
    """Selects the appropriate response template and strategy based on the query and results."""
    
    def select_template(self, query: str, num_results: int) -> dict:
        """
        Returns a dictionary containing the system prompt and instructions for the LLM.
        """
        if num_results == 0:
            return {
                "posture": "apologetic",
                "system_prompt": "You are a helpful AI movie curator. The user searched for a movie, but the system found 0 results. Apologize politely and suggest they try a different search or broader terms. Keep it to 1 or 2 sentences."
            }
        elif num_results == 1:
            return {
                "posture": "confident",
                "system_prompt": "You are a helpful AI movie curator. The system found exactly 1 perfect match for the user's query. Present this movie enthusiastically. Mention its title and why it matches (using the provided reasons). Keep it to 2 sentences."
            }
        else:
            return {
                "posture": "curated",
                "system_prompt": "You are a helpful AI movie curator. The system found multiple great matches for the user's query. Enthusiastically present the TOP 1 or 2 movies from the provided list, mentioning their titles and why they match (using the provided reasons). Mention that there are other great options in the list below. Do NOT invent movies or reasons. Keep it to 2 or 3 sentences."
            }
