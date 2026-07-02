"""
STREAMORA AI - Agent Tools

These functions are the "skills" that the Orchestrator Agent can use
to interact with the underlying microservices.
"""
import requests

def get_recommendations(user_id: int, exclude_ids: list[int] = None) -> dict:
    """Hits the Ranking Service (Port 8001) for personalized recommendations."""
    print(f"Agent Tool: Fetching recommendations for User {user_id}")
    try:
        req = {"user_id": user_id, "top_k_retrieval": 50, "top_k_final": 20, "exclude_ids": exclude_ids or []}
        resp = requests.post("http://127.0.0.1:8001/rank", json=req, timeout=15)
        if resp.status_code == 200:
            items = resp.json()  # This is a plain list of RankedItem dicts
            return {"status": "success", "data": {"recommendations": items}}
        return {"status": "error", "message": f"Ranking API returned {resp.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_explanation(user_id: int, item_id: int) -> dict:
    """Hits the Graph RAG Service (Port 8003) to explain a recommendation."""
    print(f"Agent Tool: Fetching explanation for User {user_id}, Item {item_id}")
    try:
        req = {"user_id": user_id, "item_id": item_id}
        resp = requests.post("http://127.0.0.1:8003/explain", json=req, timeout=30)
        if resp.status_code == 200:
            return {"status": "success", "data": resp.json()}
        return {"status": "error", "message": f"RAG API returned {resp.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_trending() -> dict:
    """Hits the Feature Store / Event Processor (Port 8002) for global trending items."""
    print("Agent Tool: Fetching global trending items")
    try:
        resp = requests.get("http://127.0.0.1:8002/features/global", timeout=2)
        if resp.status_code == 200:
            return {"status": "success", "data": resp.json()}
        return {"status": "error", "message": f"Feature Store returned {resp.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

import pandas as pd
import os

def search_movie_by_title(title_query: str) -> dict:
    """Searches local movies.csv for a fuzzy title match and returns item_id and title."""
    print(f"Agent Tool: Searching for movie '{title_query}'")
    try:
        if os.path.exists("data/raw/movies.csv"):
            df = pd.read_csv("data/raw/movies.csv")
            # Simple case-insensitive substring match
            matches = df[df['title'].str.contains(title_query, case=False, na=False)]
            if not matches.empty:
                first_match = matches.iloc[0]
                return {"status": "success", "item_id": int(first_match['item_id']), "title": str(first_match['title'])}
        return {"status": "error", "message": f"Could not find movie matching '{title_query}'"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_similar_movies(item_id: int, exclude_ids: list[int] = None) -> dict:
    """Hits the Ranking Service (Port 8001) for item-to-item similarity."""
    print(f"Agent Tool: Fetching similar movies for Item {item_id}")
    try:
        req = {"item_id": item_id, "top_k": 20, "exclude_ids": exclude_ids or []}
        resp = requests.post("http://127.0.0.1:8001/similar", json=req, timeout=15)
        if resp.status_code == 200:
            return {"status": "success", "data": resp.json()}
        return {"status": "error", "message": f"Ranking API returned {resp.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_similarity_explanation(source_item_id: int, target_item_id: int) -> dict:
    """Hits the Graph RAG Service (Port 8003) to explain why two items are similar."""
    print(f"Agent Tool: Explaining similarity between {source_item_id} and {target_item_id}")
    try:
        req = {"source_item_id": source_item_id, "target_item_id": target_item_id}
        resp = requests.post("http://127.0.0.1:8003/explain_similarity", json=req, timeout=30)
        if resp.status_code == 200:
            return {"status": "success", "data": resp.json()}
        return {"status": "error", "message": f"RAG API returned {resp.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def search_semantic_vector(query: str, exclude_ids: list[int] = None) -> dict:
    """Hits the Ranking Service (Port 8001) for direct semantic search against plot vectors."""
    print(f"Agent Tool: Searching semantically for '{query}'")
    try:
        req = {"query": query, "top_k": 20, "exclude_ids": exclude_ids or []}
        resp = requests.post("http://127.0.0.1:8001/search", json=req, timeout=15)
        if resp.status_code == 200:
            return {"status": "success", "data": resp.json()}
        return {"status": "error", "message": f"Ranking Search API returned {resp.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
