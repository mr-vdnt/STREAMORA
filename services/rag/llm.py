"""
AURORA AI - LLM Provider for RAG Explanations

Abstract interface for LLM operations, allowing us to swap
local models (Flan-T5) with APIs (OpenAI/Gemini) in the future.
"""

from abc import ABC, abstractmethod
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

class LLMProvider(ABC):
    @abstractmethod
    def generate_explanation(self, user_context: str, movie_title: str, graph_path: list[str]) -> str:
        """Generates a natural language explanation for why a movie was recommended."""
        pass


class LocalFlanLLM(LLMProvider):
    def __init__(self, model_name="google/flan-t5-small"):
        print(f"Loading local LLM ({model_name})...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        print("LLM loaded.")
        
    def generate_explanation(self, user_context: str, movie_title: str, graph_path: list[str]) -> str:
        if not graph_path:
            prompt = f"Explain why the movie '{movie_title}' is recommended for a user who likes {user_context}."
        else:
            path_str = ", ".join(graph_path)
            prompt = (
                f"A user likes {user_context}. We recommended '{movie_title}'. "
                f"The connection is: {path_str}. "
                f"Explain this recommendation briefly in one sentence."
            )
            
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(**inputs, max_length=60)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)


# Singleton instance
llm_provider = LocalFlanLLM()
