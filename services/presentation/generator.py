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
                ],
                keep_alive="1h"
            )
            t1 = time.time()
            return resp['message']['content'].strip(), int((t1 - t0) * 1000)
        except Exception as e:
            print(f"LLM Generation failed: {e}")
            return render_plan.get("intro", "I found some movies you might enjoy!"), 0

    def generate_stream(self, query: str, template: dict, render_plan: Dict[str, Any]):
        """
        Generates the response text as a stream of token and metric dictionaries.
        """
        import time
        t0 = time.time()
        
        if render_plan.get("strategy") == "deterministic":
            yield {"type": "token", "value": render_plan.get("intro", "Here are your results.")}
            yield {"type": "metric", "key": "llm_generation_ms", "value": 0}
            return
            
        system_prompt = template["system_prompt"]
        items = render_plan.get("items", [])
        
        context_lines = []
        for item in items:
            reasons_str = ", ".join(item.get("explanations", []))
            context_lines.append(f"- {item['title']} (Reasons: {reasons_str})")
        context_str = "\n".join(context_lines)
            
        user_prompt = f"User Query: '{query}'\n\nProvided Movies to Recommend:\n{context_str}\n\nPlease generate the response now following your system instructions."
        
        try:
            resp_stream = ollama.chat(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                keep_alive="1h",
                stream=True
            )
            
            first_token = True
            for chunk in resp_stream:
                if first_token:
                    ttft_ms = int((time.time() - t0) * 1000)
                    yield {"type": "metric", "key": "ttft_ms", "value": ttft_ms}
                    first_token = False
                    
                content = chunk.get('message', {}).get('content', '')
                if content:
                    yield {"type": "token", "value": content}
                    
                if chunk.get("done"):
                    total_ms = int((time.time() - t0) * 1000)
                    eval_count = chunk.get("eval_count", 0)
                    prompt_eval_count = chunk.get("prompt_eval_count", 0)
                    
                    yield {"type": "metric", "key": "llm_generation_ms", "value": total_ms}
                    yield {"type": "metric", "key": "completion_tokens", "value": eval_count}
                    yield {"type": "metric", "key": "prompt_tokens", "value": prompt_eval_count}
                    if total_ms > 0:
                        yield {"type": "metric", "key": "tokens_per_second", "value": round((eval_count / total_ms) * 1000, 2)}
        except Exception as e:
            print(f"LLM Generation Stream failed: {e}")
            yield {"type": "token", "value": render_plan.get("intro", "I found some movies you might enjoy!")}
            yield {"type": "metric", "key": "llm_generation_ms", "value": 0}
