import ollama
from typing import List

class ResponseGenerator:
    """Generates the natural language response using Ollama, strictly following templates."""
    
    def __init__(self, model_name: str = "llama3.2:latest"):
        self.model = model_name
        
    def generate(self, query: str, template: dict, context_data: List[dict]) -> str:
        """
        Generates the response text.
        context_data is a list of dictionaries containing 'title' and 'reasons'.
        """
        system_prompt = template["system_prompt"]
        
        # Build the context string
        if not context_data:
            context_str = "No movies were found."
        else:
            context_lines = []
            for item in context_data:
                context_lines.append(f"- {item['title']} (Reasons: {item['reasons']})")
            context_str = "\n".join(context_lines)
            
        user_prompt = f"User Query: '{query}'\n\nProvided Movies to Recommend:\n{context_str}\n\nPlease generate the response now following your system instructions."
        
        try:
            resp = ollama.chat(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ]
            )
            return resp['message']['content'].strip()
        except Exception as e:
            print(f"LLM Generation failed: {e}")
            # Fallback responses
            if template["posture"] == "apologetic":
                return "I couldn't find anything matching that in our current catalog."
            elif template["posture"] == "confident":
                return f"I found the perfect match: {context_data[0]['title']}!"
            else:
                return f"I found {len(context_data)} movies you might enjoy, starting with {context_data[0]['title']}!"
