import os
import json
import re
import requests
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from services.agent.tools import get_explanation
import ollama

import csv

movies_db = {}
if os.path.exists("data/raw/movies.csv"):
    with open("data/raw/movies.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                iid = int(row.get('item_id', 0))
                movies_db[iid] = row
            except ValueError:
                pass

def _get_movie_metadata(row):
    title = row.get('title', 'Unknown')
    
    # Extract year if present in title (e.g. 'Inception (2010)')
    year = ""
    if '(' in title:
        year = title.split('(')[-1].strip(')')
        
    # Rating logic
    try:
        rating = float(row.get('rating', 8.0))
    except ValueError:
        rating = 8.0
        
    is_adult = str(row.get('is_adult', 'False')).lower() == 'true'
    
    return {
        "title": title,
        "year": year,
        "match_percentage": int(rating * 10),
        "runtime": f"{row.get('runtime', 120)} min",
        "audience_type": "Adult" if is_adult else "Family/General",
        "tags": str(row.get('genres', '')).split('|'),
        "story_summary": row.get('overview', 'No summary available.'),
        "why_recommended": "Recommended by Streamora AI",
        "director": row.get('director', 'Unknown'),
        "tmdb_id": int(float(row.get('tmdb_id', 0))) if row.get('tmdb_id') else 0,
        "trailer_url": row.get('trailer_url', '')
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
        print("Loading Query Intelligence Engine...")
        self.conversation_memory = {}
        self.model = 'llama3'
        from services.agent.query_intelligence import QueryIntelligenceEngine
        self.query_engine = QueryIntelligenceEngine(movies_db)

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

        # Use Deterministic NLP Pipeline (No LLM)
        context = self.conversation_memory.get(user_id, {}).get("last_entities", {})
        query_plan = self.query_engine.parse(query, context=context)
        
        # Save session context
        if user_id not in self.conversation_memory:
            self.conversation_memory[user_id] = {}
        self.conversation_memory[user_id]["last_entities"] = query_plan["entities"]
        
        # If it's pure chat, bypass search engine completely
        if query_plan["intent"] == "chat":
            try:
                resp = ollama.chat(model=self.model, messages=[{'role': 'user', 'content': query}])
                llm_text = resp['message']['content']
            except:
                llm_text = "I'm your AI movie curator! Ask me for recommendations."
            return {
                "query": query,
                "intent": "chat",
                "response": [],
                "llm_response": llm_text,
                "entities": query_plan["entities"]
            }
        
        payload = {
            "query": query,
            "target_genres": query_plan["entities"].get("genres", []),
            "target_moods": query_plan["entities"].get("themes", []),
            "target_actors": query_plan["entities"].get("actors", []),
            "target_director": query_plan["entities"]["directors"][0] if query_plan["entities"].get("directors") else "",
            "target_content_type": "",
            "top_k": 15,
            "exclude_ids": exclude_ids
        }
        
        response_data = []
        try:
            from services.ranking.main import search_semantic, SearchRequest, movies_db
            from services.catalog.ingestion import ingest_from_tmdb
            
            # Construct SearchRequest explicitly
            ranking_req = SearchRequest(
                query=payload["query"],
                target_genres=payload["target_genres"],
                target_moods=payload["target_moods"],
                target_actors=payload["target_actors"],
                target_director=payload["target_director"],
                target_content_type=payload["target_content_type"],
                top_k=payload["top_k"],
                exclude_ids=payload["exclude_ids"]
            )
            
            # Direct internal function call instead of slow network requests!
            ranked_items = search_semantic(ranking_req)
            
            # If nothing found locally, blast TMDB live INGESTION!
            if not ranked_items:
                print("Missing locally, triggering TMDB Ingestion...")
                new_iid = ingest_from_tmdb(query)
                if new_iid:
                    print(f"Ingested ID {new_iid}. Re-running search.")
                    ranked_items = search_semantic(ranking_req)
            
            for item in ranked_items:
                iid = item.item_id
                if iid not in movies_db: continue
                r = movies_db[iid]
                
                rich_meta = _get_movie_metadata(r)
                if item.explanation:
                    rich_meta["why_recommended"] = " • ".join(item.explanation)
                
                response_data.append({
                    "item_id": iid,
                    "title": r['title'],
                    "poster_url": r.get('poster_url', ''),
                    "backdrop_url": r.get('backdrop_url', ''),
                    "overview": r.get('overview', ''),
                    "rich_metadata": rich_meta,
                    "explanation": rich_meta.get("why_recommended", "")
                })
                
        except Exception as e:
            import traceback
            traceback.print_exc()
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
