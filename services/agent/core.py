import os
import json
import re
import requests
import pandas as pd
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from services.agent.tools import get_explanation
import ollama

movies_df = None
if os.path.exists("data/raw/movies.csv"):
    movies_df = pd.read_csv("data/raw/movies.csv")
    movies_df['genres'] = movies_df['genres'].fillna('')
    movies_df['cast'] = movies_df['cast'].fillna('')
    movies_df['director'] = movies_df['director'].fillna('')
    movies_df['moods'] = movies_df['moods'].fillna('')
    movies_df['themes'] = movies_df['themes'].fillna('')

def _get_movie_metadata(row):
    return {
        "title": row.get('title', 'Unknown'),
        "year": str(row.get('title', '')).split('(')[-1].strip(')') if '(' in str(row.get('title', '')) else "",
        "match_percentage": int(row.get('rating', 8.0) * 10),
        "runtime": f"{row.get('runtime', 120)} min",
        "audience_type": "Adult" if row.get('is_adult') == True else "Family/General",
        "tags": str(row.get('genres', '')).split('|'),
        "story_summary": row.get('overview', 'No summary available.'),
        "why_recommended": "Recommended by Streamora AI",
        "director": row.get('director', 'Unknown'),
        "tmdb_id": int(row.get('tmdb_id', 0)) if pd.notna(row.get('tmdb_id')) else 0,
        "trailer_url": row.get('trailer_url', '') if pd.notna(row.get('trailer_url')) else ''
    }

class ExtractionSchema(BaseModel):
    intent: str
    target_genres: List[str]
    target_moods: List[str]
    target_actors: List[str]
    target_director: str
    target_content_type: str

class OrchestratorAgent:
    def __init__(self):
        print("Loading AI Discovery Engine (Ollama)...")
        self.conversation_memory = {}
        self.model = 'llama3'
        
    def _extract_entities(self, query: str):
        prompt = f"""
        Extract the following information from the user's movie search query: "{query}"
        - intent: What is the user looking for? (e.g. "search", "recommendation", "similar")
        - target_genres: List of genres (e.g. Action, Sci-Fi)
        - target_moods: List of moods/themes (e.g. Dark, Mind-bending, Space)
        - target_actors: List of actors mentioned
        - target_director: Any director mentioned
        - target_content_type: "movie", "series", "anime", or "documentary"
        """
        try:
            resp = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                format=ExtractionSchema.model_json_schema()
            )
            data = json.loads(resp['message']['content'])
            return data
        except Exception as e:
            print(f"Extraction failed: {e}")
            return {
                "intent": "search",
                "target_genres": [],
                "target_moods": [],
                "target_actors": [],
                "target_director": "",
                "target_content_type": ""
            }

    def process_query(self, user_id: int, query: str, exclude_ids: list[int] = None) -> dict:
        if exclude_ids is None:
            exclude_ids = []
            
        lower_q = query.lower()
        if "why" in lower_q or "explain" in lower_q:
            match = re.search(r'\b\d+\b', query)
            item_id = int(match.group(0)) if match else 1
            tool_resp = get_explanation(user_id, item_id)
            return {
                "query": query,
                "intent": "explanation",
                "response": [],
                "llm_response": tool_resp["data"]["explanation"] if tool_resp["status"] == "success" else "High relevance based on semantic matching.",
                "entities": {}
            }

        entities = self._extract_entities(query)
        
        payload = {
            "query": query,
            "target_genres": entities.get("target_genres", []),
            "target_moods": entities.get("target_moods", []),
            "target_actors": entities.get("target_actors", []),
            "target_director": entities.get("target_director", ""),
            "target_content_type": entities.get("target_content_type", ""),
            "top_k": 15,
            "exclude_ids": exclude_ids
        }
        
        response_data = []
        try:
            resp = requests.post("http://127.0.0.1:8001/search", json=payload, timeout=10)
            if resp.status_code == 200:
                ranked_items = resp.json()
                for item in ranked_items:
                    iid = item["item_id"]
                    if movies_df is None: continue
                    row = movies_df[movies_df['item_id'] == iid]
                    if row.empty: continue
                    r = row.iloc[0]
                    
                    rich_meta = _get_movie_metadata(r)
                    if item.get("explanation"):
                        rich_meta["why_recommended"] = " • ".join(item["explanation"])
                    
                    response_data.append({
                        "item_id": iid,
                        "title": r['title'],
                        "poster_url": r.get('poster_url', ''),
                        "backdrop_url": r.get('backdrop_url', ''),
                        "overview": r.get('overview', ''),
                        "rich_metadata": rich_meta,
                        "explanation": rich_meta["why_recommended"]
                    })
        except Exception as e:
            print(f"Hybrid Search Failed: {e}")

        # Context Builder & LLM Response
        if not response_data:
            llm_text = "I couldn't find anything matching that in our current catalog."
        else:
            context_titles = [f"- {m['title']}: {m['overview'][:100]}..." for m in response_data[:5]]
            prompt = f"The user asked: '{query}'. Based on our hybrid search, we found these movies:\n" + "\n".join(context_titles) + "\nWrite a short, engaging 2-sentence response as a personal AI movie curator recommending these titles."
            try:
                resp = ollama.chat(
                    model=self.model,
                    messages=[{'role': 'user', 'content': prompt}]
                )
                llm_text = resp['message']['content']
            except Exception as e:
                llm_text = f"I found {len(response_data)} movies you might enjoy!"

        return {
            "query": query,
            "intent": entities.get("intent", "search"),
            "response": response_data,
            "llm_response": llm_text,
            "entities": entities
        }

agent = OrchestratorAgent()
