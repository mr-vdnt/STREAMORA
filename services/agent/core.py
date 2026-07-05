"""
STREAMORA AI - Netflix-Level Orchestrator Agent
"""
import os
import re
import json
import requests
import pandas as pd
from services.agent.tools import get_explanation

# --- Global Knowledge Graph / Entity Lexicon ---
movies_df = None
ENTITY_LEXICON = {
    "genres": set(),
    "moods": set(),
    "actors": set(),
    "directors": set(),
    "themes": set()
}

if os.path.exists("data/raw/movies.csv"):
    movies_df = pd.read_csv("data/raw/movies.csv")
    movies_df['genres'] = movies_df['genres'].fillna('')
    movies_df['cast'] = movies_df['cast'].fillna('')
    movies_df['director'] = movies_df['director'].fillna('')
    movies_df['moods'] = movies_df['moods'].fillna('')
    movies_df['themes'] = movies_df['themes'].fillna('')
    
    for _, row in movies_df.iterrows():
        # Genres
        for g in str(row['genres']).split('|'):
            if g.strip(): ENTITY_LEXICON["genres"].add(g.strip().lower())
        # Moods
        for m in str(row['moods']).split('|'):
            if m.strip(): ENTITY_LEXICON["moods"].add(m.strip().lower())
        # Themes
        for t in str(row['themes']).split('|'):
            if t.strip(): ENTITY_LEXICON["themes"].add(t.strip().lower())
        # Cast
        for a in str(row['cast']).split(','):
            if a.strip(): ENTITY_LEXICON["actors"].add(a.strip().lower())
        # Director
        for d in str(row['director']).split(','):
            if d.strip(): ENTITY_LEXICON["directors"].add(d.strip().lower())

def _get_movie_metadata(row):
    """Helper to safely extract movie metadata for UI."""
    return {
        "title": row.get('title', 'Unknown'),
        "year": str(row.get('title', '')).split('(')[-1].strip(')') if '(' in str(row.get('title', '')) else "",
        "match_percentage": int(row.get('rating', 8.0) * 10),
        "runtime": f"{row.get('runtime', 120)} min",
        "audience_type": "Adult" if row.get('is_adult') == True else "Family/General",
        "tags": str(row.get('genres', '')).split('|'),
        "story_summary": row.get('overview', 'No summary available.'),
        "why_recommended": "Recommended by Streamora Hybrid Engine",
        "director": row.get('director', 'Unknown')
    }

class OrchestratorAgent:
    def __init__(self):
        print("Loading NLP Intent & Entity Parser...")
        self.conversation_memory = {}
        print("Agent ready.")
        
    def _extract_entities(self, query: str):
        query_lower = query.lower()
        
        target_content_type = ""
        if re.search(r'\b(movie|film|movies|films)\b', query_lower): target_content_type = "movie"
        elif re.search(r'\b(series|show|shows|tv)\b', query_lower): target_content_type = "series"
        elif re.search(r'\b(anime)\b', query_lower): target_content_type = "anime"
        elif re.search(r'\b(documentary|documentaries)\b', query_lower): target_content_type = "documentary"

        target_genres = [g for g in ENTITY_LEXICON["genres"] if g in query_lower]
        target_moods = [m for m in ENTITY_LEXICON["moods"] if m in query_lower]
        target_themes = [t for t in ENTITY_LEXICON["themes"] if t in query_lower]
        target_actors = [a for a in ENTITY_LEXICON["actors"] if a in query_lower]
        target_directors = [d for d in ENTITY_LEXICON["directors"] if d in query_lower]
        
        # Combine moods and themes
        target_moods.extend(target_themes)
        
        return {
            "target_genres": target_genres,
            "target_moods": list(set(target_moods)),
            "target_actors": target_actors,
            "target_director": target_directors[0] if target_directors else "",
            "target_content_type": target_content_type
        }

    def process_query(self, user_id: int, query: str, exclude_ids: list[int] = None) -> dict:
        if exclude_ids is None:
            exclude_ids = []
            
        lower_q = query.lower()
        
        # 1. Handle Explicit Explanations First
        if "why" in lower_q or "explain" in lower_q:
            match = re.search(r'\b\d+\b', query)
            item_id = int(match.group(0)) if match else 1
            tool_resp = get_explanation(user_id, item_id)
            return {
                "query": query,
                "intent": "explanation",
                "response": tool_resp["data"]["explanation"] if tool_resp["status"] == "success" else "High relevance based on semantic matching."
            }

        # 2. Query Planner & Entity Extraction
        entities = self._extract_entities(query)
        
        payload = {
            "query": query,
            "target_genres": entities["target_genres"],
            "target_moods": entities["target_moods"],
            "target_actors": entities["target_actors"],
            "target_director": entities["target_director"],
            "target_content_type": entities["target_content_type"],
            "top_k": 15,
            "exclude_ids": exclude_ids
        }
        
        # 3. Request Hybrid Ranking Service
        response_data = []
        try:
            resp = requests.post("http://127.0.0.1:8001/search", json=payload, timeout=5)
            if resp.status_code == 200:
                ranked_items = resp.json()
                # 4. Context Builder & Grounding
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

        # If zero matches found, DO NOT fallback to random movies.
        # Return empty list, UI will render "No matches found" gracefully.
        
        return {
            "query": query,
            "intent": "hybrid_search",
            "response": response_data,
            "entities": entities
        }

agent = OrchestratorAgent()
