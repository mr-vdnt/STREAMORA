"""
STREAMORA AI - Agent Core Logic

Uses NLP to classify user intent and route to the correct tool.
"""
import os
import re
import pandas as pd
from services.agent.tools import get_recommendations, get_explanation, get_trending, search_movie_by_title, get_similar_movies, search_semantic_vector

# Load movies DB once globally
movies_df = None
if os.path.exists("data/raw/movies.csv"):
    movies_df = pd.read_csv("data/raw/movies.csv")
    movies_df['genres'] = movies_df['genres'].fillna('')
    movies_df['overview'] = movies_df['overview'].fillna('')
    def generate_tags(row):
        text = str(row['genres']).lower() + " " + str(row['overview']).lower()
        tags = set(row['genres'].split('|'))
        if 'space' in text or 'alien' in text: tags.add('Space Exploration')
        if 'time travel' in text or 'time loop' in text: tags.add('Time Travel')
        if 'cyber' in text or 'hacker' in text: tags.add('Cyberpunk')
        if 'psychological' in text or 'mind' in text: tags.add('Mind-Bending')
        if 'dark' in text or 'grim' in text: tags.add('Dark')
        if 'crime' in text or 'murder' in text or 'detective' in text: tags.add('Crime Masterpieces')
        if 'political' in text or 'president' in text: tags.add('Political Intrigue')
        if 'history' in text or 'war' in text: tags.add('Historical Fiction')
        if 'heart' in text or 'feel-good' in text or 'family' in text: tags.add('Feel-Good')
        if 'epic' in text or 'journey' in text: tags.add('Epic Adventures')
        return "|".join(tags)
    movies_df['rich_tags'] = movies_df.apply(generate_tags, axis=1)

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

    def _validate_and_enrich(self, raw_items: list, query: str = "", exclude_ids: list[int] = None, top_k: int = 15, base_explanation: str = "Recommended by Streamora AI.") -> list:
        if exclude_ids is None: exclude_ids = []
        if movies_df is None: return []
        
        lower_q = query.lower()
        
        target_content_type = None
        if "movie" in lower_q or "film" in lower_q: target_content_type = "movie"
        elif "series" in lower_q or "show" in lower_q: target_content_type = "series"
        elif "anime" in lower_q: target_content_type = "anime"
        elif "documentary" in lower_q or "documentaries" in lower_q: target_content_type = "documentary"
        
        valid_genres = ["action", "comedy", "horror", "drama", "romance", "thriller", "animation", "sci-fi", "science fiction", "psychological", "family", "crime"]
        target_genre = next((g for g in valid_genres if g in lower_q), None)
        if target_genre == "sci-fi": target_genre = "sci"
        
        enriched = []
        for item in raw_items:
            iid = item.get("item_id", 0) if isinstance(item, dict) else int(item)
            if iid in exclude_ids: continue
            
            row = movies_df[movies_df['item_id'] == iid]
            if row.empty: continue
            
            r = row.iloc[0]
            
            item_type = str(r.get("content_type", "")).lower()
            if target_content_type:
                if target_content_type == "series" and "series" not in item_type: continue
                elif target_content_type != "series" and item_type != target_content_type: continue
                
            item_genres = str(r.get("genres", "")).lower()
            if target_genre and target_genre not in item_genres:
                continue
                
            if not r.get("title") or pd.isna(r.get("title")): continue
            if not r.get("poster_url") or pd.isna(r.get("poster_url")): continue

            enriched.append({
                "item_id": int(iid),
                "title": str(r['title']),
                "poster_url": str(r.get('poster_url', '')),
                "backdrop_url": str(r.get('backdrop_url', '')),
                "overview": str(r.get('overview', '')),
                "rich_metadata": _get_movie_metadata(r),
                "explanation": base_explanation
            })
            if len(enriched) >= top_k: break
                
        return enriched

    def process_query(self, user_id: int, query: str, exclude_ids: list[int] = None) -> dict:
        if exclude_ids is None:
            exclude_ids = []
            
        if user_id not in self.conversation_memory:
            self.conversation_memory[user_id] = []
        self.conversation_memory[user_id].append(query)
        
        context_query = " ".join(self.conversation_memory[user_id][-3:])
        
        top_intent = "recommendation" # Default
        
        lower_q = query.lower()
        context_lower = context_query.lower()
        
        if "similar" in lower_q or "like" in lower_q:
            top_intent = "similar_movies"
        elif "trend" in lower_q or "popular" in lower_q or "hot" in lower_q:
            top_intent = "trending"
        elif "why" in lower_q or "explain" in lower_q:
            top_intent = "explanation"
        elif any(g in lower_q for g in ["horror", "comedy", "action", "thriller", "drama", "anime", "sci-fi", "romance", "psychological", "family", "mind-bending", "dark", "crime", "space", "time travel", "epic", "feel-good", "historical", "hidden gems"]):
            top_intent = "category_cluster"
        elif "recommend" in lower_q:
            top_intent = "recommendation"
        elif any(g in context_lower for g in ["horror", "comedy", "action", "thriller", "drama", "anime", "sci-fi", "romance"]):
            if top_intent == "recommendation" and "similar" not in lower_q:
                top_intent = "category_cluster"
                lower_q = context_lower
                
        print(f"Agent classified intent: '{top_intent}'")
        response_data = None
        
        if top_intent == "category_cluster":
            # Direct semantic vector search against FAISS plot embeddings
            tool_resp = search_semantic_vector(query, exclude_ids)
            if tool_resp["status"] == "success":
                similar_items = tool_resp["data"]
                response_data = self._validate_and_enrich(
                    similar_items, query, exclude_ids, 15,
                    f"Recommended for query '{query}' based on plot similarity and validated attributes."
                )
            else:
                response_data = []

        elif top_intent == "similar_movies":
            title_query = self._extract_movie_title(query)
            search_res = search_movie_by_title(title_query)
            if search_res["status"] == "success":
                source_id = search_res["item_id"]
                sim_resp = get_similar_movies(source_id, exclude_ids)
                if sim_resp["status"] == "success":
                    similar_items = sim_resp["data"]
                    response_data = self._validate_and_enrich(
                        similar_items, query, exclude_ids, 15,
                        f"Similar to {search_res['title']} based on semantic embeddings and validated attributes."
                    )
                else:
                    # Fallback to genre-matching similar movies
                    if movies_df is not None:
                        matched_genre = "Drama"
                        source_row = movies_df[movies_df['item_id'] == source_id]
                        if not source_row.empty:
                            genres = str(source_row.iloc[0]['genres']).split('|')
                            if genres: matched_genre = genres[0]
                        
                        sim_movies = movies_df[movies_df['genres'].str.contains(matched_genre, na=False)].sort_values(by='rating', ascending=False).head(30)
                        enriched = []
                        for _, r in sim_movies.iterrows():
                            iid = int(r['item_id'])
                            if iid in exclude_ids or iid == source_id: continue
                            enriched.append({
                                "item_id": iid,
                                "title": r['title'],
                                "poster_url": r.get('poster_url', ''),
                                "backdrop_url": r.get('backdrop_url', ''),
                                "overview": r.get('overview', ''),
                                "rich_metadata": _get_movie_metadata(r),
                                "explanation": f"Similar to {search_res['title']} based on genre and rating."
                            })
                        response_data = enriched
                    else:
                        response_data = []
            else:
                # Fallback: search failed, return popular movies
                if movies_df is not None:
                    top_movies = movies_df.sort_values(by='rating', ascending=False).head(15)
                    response_data = []
                    for _, r in top_movies.iterrows():
                        iid = int(r['item_id'])
                        if iid in exclude_ids: continue
                        response_data.append({
                            "item_id": iid,
                            "title": r['title'],
                            "poster_url": r.get('poster_url', ''),
                            "backdrop_url": r.get('backdrop_url', ''),
                            "overview": r.get('overview', ''),
                            "rich_metadata": _get_movie_metadata(r),
                            "explanation": "Recommended by Streamora AI."
                        })
                else:
                    response_data = []

        elif top_intent == "recommendation":
            tool_resp = get_recommendations(user_id, exclude_ids)
            if tool_resp["status"] == "success":
                raw_items = tool_resp["data"]["recommendations"]
                response_data = self._validate_and_enrich(
                    raw_items, query, exclude_ids, 15,
                    "Recommended because it aligns strongly with your preferences and passes strict validation."
                )
            else:
                # Fallback to generic recommendations (top rated)
                if movies_df is not None:
                    top_movies = movies_df.sort_values(by='rating', ascending=False).head(30)
                    enriched = []
                    for _, r in top_movies.iterrows():
                        iid = int(r['item_id'])
                        if iid in exclude_ids: continue
                        enriched.append({
                            "item_id": iid,
                            "title": r['title'],
                            "poster_url": r.get('poster_url', ''),
                            "backdrop_url": r.get('backdrop_url', ''),
                            "overview": r.get('overview', ''),
                            "rich_metadata": _get_movie_metadata(r),
                            "explanation": "Recommended because it is highly rated globally."
                        })
                    response_data = enriched
                else:
                    response_data = []
                
        elif top_intent == "explanation":
            item_id = self._extract_item_id(query)
            tool_resp = get_explanation(user_id, item_id)
            if tool_resp["status"] == "success":
                response_data = tool_resp["data"]["explanation"]
            else:
                response_data = f"This movie has a high recommendation score because it fits perfectly with your preferred genres."
                
        elif top_intent == "trending":
            tool_resp = get_trending()
            if tool_resp["status"] == "success":
                trends = tool_resp["data"]["popular_items"]
                response_data = []
                for t in trends:
                    item_id = t[0]
                    if item_id in exclude_ids: continue
                    if len(response_data) >= 15: break
                    if movies_df is not None:
                        row = movies_df[movies_df['item_id'] == item_id]
                        if not row.empty:
                            r = row.iloc[0]
                            response_data.append({
                                "item_id": item_id, 
                                "score": t[1], 
                                "title": r['title'],
                                "poster_url": r.get('poster_url', ''),
                                "backdrop_url": r.get('backdrop_url', ''),
                                "overview": r.get('overview', ''),
                                "rich_metadata": _get_movie_metadata(r),
                                "explanation": "Trending globally across the platform right now."
                            })
                response_data = response_data
            else:
                # Fallback to generic popular movies
                if movies_df is not None:
                    top_movies = movies_df.sort_values(by='popularity', ascending=False).head(30)
                    response_data = []
                    for _, r in top_movies.iterrows():
                        iid = int(r['item_id'])
                        if iid in exclude_ids: continue
                        response_data.append({
                            "item_id": iid,
                            "title": r['title'],
                            "poster_url": r.get('poster_url', ''),
                            "backdrop_url": r.get('backdrop_url', ''),
                            "overview": r.get('overview', ''),
                            "rich_metadata": _get_movie_metadata(r),
                            "explanation": "Trending globally across the platform right now."
                        })
                    response_data = response_data
                else:
                    response_data = []
                
        return {
            "query": query,
            "intent": top_intent,
            "response": response_data
        }

agent = OrchestratorAgent()
