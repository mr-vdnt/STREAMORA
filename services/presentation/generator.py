import ollama
from typing import Dict, Any

class ResponseGenerator:
    """Generates natural language responses using an LLM according to a defined plan and template."""
    
    def __init__(self, model_name: str = "llama3"):
        self.model = model_name
        
    def generate(self, query: str, template: dict, render_plan: Dict[str, Any]) -> str:
        """
        Generates the response text.
        """
        # 1. Deterministic Bypass
        if render_plan.get("strategy") == "deterministic":
            return render_plan.get("intro", "Here are your results."), 0
            
        # 2. LLM Generation
        system_prompt = template["system_prompt"]
        items = render_plan.get("items", [])
        
        context_lines = []
        for item in items:
            reasons_str = ", ".join(item.get("explanations", []))
            context_lines.append(f"- {item['title']} (Reasons: {reasons_str})")
        context_str = "\n".join(context_lines)
            
        user_prompt = f"User Query: '{query}'\n\nProvided Movies to Recommend:\n{context_str}\n\nPlease generate the response now following your system instructions."
        
        try:
            import time
            t0 = time.time()
            resp = ollama.chat(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ]
            )
            t1 = time.time()
            return resp['message']['content'].strip(), int((t1 - t0) * 1000)
        except Exception as e:
            print(f"LLM Generation failed: {e}")
            return render_plan.get("intro", "I found some movies you might enjoy!"), 0
