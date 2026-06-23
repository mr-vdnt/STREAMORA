"""
AURORA AI - Agent Core Logic

Uses NLP to classify user intent and route to the correct tool.
"""
import os
import re
import pandas as pd
from services.agent.tools import get_recommendations, get_explanation, get_trending, search_movie_by_title, get_similar_movies

# Load movies DB once globally
movies_df = None
if os.path.exists("data/raw/movies.csv"):
    movies_df = pd.read_csv("data/raw/movies.csv")

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
        "why_recommended": f"Recommended because it matches your selected criteria and shares thematic elements with popular titles in this category.",
        "director": row.get('director', 'Unknown')
    }

class OrchestratorAgent:
    def __init__(self):
        print("Loading Agent Intent Classifier (Mock rules to save 250MB RAM)...")
        self.intents = ["recommendation", "explanation", "trending", "similar_movies", "genre_search"]
        self.conversation_memory = {} # {user_id: [history]}
        print("Agent ready.")
        
    def _extract_item_id(self, query: str) -> int:
        match = re.search(r'\b\d+\b', query)
        if match:
            return int(match.group(0))
        return 1
        
    def _extract_movie_title(self, query: str) -> str:
        query = query.replace('"', '').replace("'", "")
        stopwords = ["recommend", "movie", "movies", "similar", "to", "like", "what", "are", "show", "me", "some"]
        words = query.split()
        title_words = [w for w in words if w.lower() not in stopwords]
        return " ".join(title_words) if title_words else "Toy Story"

    def process_query(self, user_id: int, query: str) -> dict:
        if user_id not in self.conversation_memory:
            self.conversation_memory[user_id] = []
        self.conversation_memory[user_id].append(query)
        
        # Analyze history for context
        context_query = " ".join(self.conversation_memory[user_id][-3:])
        
        top_intent = "recommendation" # Default
        
        # Heuristic overrides for better accuracy
        lower_q = query.lower()
        context_lower = context_query.lower()
        
        if "similar" in lower_q or "like" in lower_q:
            top_intent = "similar_movies"
        elif "trend" in lower_q or "popular" in lower_q or "hot" in lower_q:
            top_intent = "trending"
        elif "why" in lower_q or "explain" in lower_q:
            top_intent = "explanation"
        elif any(g in lower_q for g in ["horror", "comedy", "action", "thriller", "drama", "anime", "k-drama", "bollywood", "romance", "psychological", "family"]):
            top_intent = "genre_search"
        elif "recommend" in lower_q:
            top_intent = "recommendation"
        elif any(g in context_lower for g in ["horror", "comedy", "action", "thriller", "drama", "anime"]):
            # Memory fallback
            if top_intent == "recommendation" and "similar" not in lower_q:
                top_intent = "genre_search"
                lower_q = context_lower # pass history to genre extractor
        elif any(g in lower_q for g in ["horror", "comedy", "action", "thriller", "drama", "anime", "k-drama", "bollywood", "romance", "psychological", "family"]):
            top_intent = "genre_search"
        elif "recommend" in lower_q:
            top_intent = "recommendation"
            
        print(f"Agent classified intent: '{top_intent}'")
        
        response_data = None
        
        if top_intent == "genre_search":
            if movies_df is not None:
                # Find matching genres or tags
                genres_list = ["horror", "comedy", "action", "thriller", "drama", "anime", "k-drama", "bollywood", "romance", "psychological", "family"]
                detected_genre = next((g for g in genres_list if g in lower_q), None)
                if not detected_genre:
                    detected_genre = lower_q.replace(" movies", "").replace(" films", "").replace(" show ", "").strip()
                    
                matched = movies_df[movies_df['genres'].str.contains(detected_genre, case=False, na=False) | movies_df['overview'].str.contains(detected_genre, case=False, na=False)]
                response_data = []
                for _, row in matched.head(20).iterrows():
                    response_data.append({
                        "item_id": int(row['item_id']),
                        "title": row['title'],
                        "poster_url": row.get('poster_url', ''),
                        "backdrop_url": row.get('backdrop_url', ''),
                        "overview": row.get('overview', ''),
                        "rich_metadata": _get_movie_metadata(row)
                    })
                if not response_data:
                    response_data = "We couldn't find any titles matching that category."
            else:
                response_data = "Database not loaded."

        elif top_intent == "similar_movies":
            title_query = self._extract_movie_title(query)
            search_res = search_movie_by_title(title_query)
            
            if search_res["status"] == "success":
                source_id = search_res["item_id"]
                source_title = search_res["title"]
                
                sim_resp = get_similar_movies(source_id)
                if sim_resp["status"] == "success":
                    similar_items = sim_resp["data"]
                    for item in similar_items:
                        # Enrich locally — no Graph RAG call (port 8003 doesn't exist on Render)
                        item["explanation"] = f"Similar to {source_title} based on shared themes and genre DNA."
                        item["rich_metadata"] = {}
                        
                        # Add poster + metadata if available in df
                        if movies_df is not None:
                            row = movies_df[movies_df['item_id'] == item['item_id']]
                            if not row.empty:
                                item["poster_url"] = row.iloc[0].get('poster_url', '')
                                item["rich_metadata"] = _get_movie_metadata(row.iloc[0])
                                
                    response_data = similar_items
                else:
                    response_data = sim_resp["message"]
            else:
                response_data = search_res["message"]

        elif top_intent == "recommendation":
            tool_resp = get_recommendations(user_id)
            if tool_resp["status"] == "success":
                raw_items = tool_resp["data"]["recommendations"]
                enriched = []
                for item in raw_items:
                    iid = item.get("item_id", 0)
                    entry = {
                        "item_id": iid,
                        "title": item.get("title", ""),
                        "poster_url": "",
                        "rich_metadata": {}
                    }
                    if movies_df is not None:
                        row = movies_df[movies_df['item_id'] == iid]
                        if not row.empty:
                            entry["title"] = row.iloc[0]['title']
                            entry["poster_url"] = row.iloc[0].get('poster_url', '')
                            entry["backdrop_url"] = row.iloc[0].get('backdrop_url', '')
                            entry["overview"] = row.iloc[0].get('overview', '')
                            entry["rich_metadata"] = _get_movie_metadata(row.iloc[0])
                    enriched.append(entry)
                response_data = enriched
            else:
                response_data = tool_resp["message"]
                
        elif top_intent == "explanation":
            item_id = self._extract_item_id(query)
            tool_resp = get_explanation(user_id, item_id)
            if tool_resp["status"] == "success":
                response_data = tool_resp["data"]["explanation"]
            else:
                response_data = tool_resp["message"]
                
        elif top_intent == "trending":
            tool_resp = get_trending()
            if tool_resp["status"] == "success":
                trends = tool_resp["data"]["popular_items"]
                response_data = []
                for t in trends:
                    item_id = t[0]
                    score = t[1]
                    title = f"Movie {item_id}"
                    poster_url = ""
                    meta = {}
                    if movies_df is not None:
                        row = movies_df[movies_df['item_id'] == item_id]
                        if not row.empty:
                            title = row.iloc[0]['title']
                            poster_url = row.iloc[0].get('poster_url', '')
                            meta = _get_movie_metadata(row.iloc[0])
                    
                    backdrop_url = ""
                    overview = ""
                    if movies_df is not None:
                        trow = movies_df[movies_df['item_id'] == item_id]
                        if not trow.empty:
                            backdrop_url = trow.iloc[0].get('backdrop_url', '')
                            overview = trow.iloc[0].get('overview', '')
                    response_data.append({
                        "item_id": item_id, 
                        "score": score, 
                        "title": title,
                        "poster_url": poster_url,
                        "backdrop_url": backdrop_url,
                        "overview": overview,
                        "rich_metadata": meta
                    })
            else:
                response_data = tool_resp["message"]
                
        return {
            "query": query,
            "intent": top_intent,
            "response": response_data
        }

agent = OrchestratorAgent()
