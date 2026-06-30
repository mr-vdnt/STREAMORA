"""
STREAMORA AI - Enterprise RAG & Graph Intelligence Service

Combines the Knowledge Graph engine and local LLM to generate
natural language explanations for recommendations.
"""

import os
import sys
import requests
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from services.graph.engine import graph_engine
from services.rag.llm import llm_provider

app = FastAPI(title="STREAMORA AI - RAG & Graph Intelligence")

# Load movies metadata for title lookup
movies_df = pd.DataFrame()
if os.path.exists("data/raw/movies.csv"):
    movies_df = pd.read_csv("data/raw/movies.csv")


class ExplainRequest(BaseModel):
    user_id: int
    item_id: int


class ExplainResponse(BaseModel):
    user_id: int
    item_id: int
    movie_title: str
    explanation: str
    graph_path: list[str]
    rich_metadata: dict


@app.on_event("startup")
async def startup_event():
    # Build graph in-memory on startup
    graph_engine.build_graph()


@app.post("/explain", response_model=ExplainResponse)
def explain_recommendation(request: ExplainRequest):
    """
    Generates a natural language explanation for why a movie was recommended.
    Internally queries the Knowledge Graph for connection paths and uses
    a local LLM to formulate the explanation text.
    """
    # 1. Get Movie Title
    title = f"Movie {request.item_id}"
    if not movies_df.empty:
        row = movies_df[movies_df['item_id'] == request.item_id]
        if not row.empty:
            title = row.iloc[0]['title']

    # 2. Get User Context (from Feature Store running on 8002)
    user_context = "movies"
    recent_items = []
    try:
        resp = requests.get(f"http://127.0.0.1:8002/features/user/{request.user_id}", timeout=2)
        if resp.status_code == 200:
            user_features = resp.json()
            top_genres = [g[0] for g in user_features.get("top_genres", [])]
            if top_genres:
                user_context = ", ".join(top_genres)
            recent_items = user_features.get("recent_items", [])
    except Exception:
        pass

    # 3. Find Graph Path
    # Since we didn't add users as explicit nodes in the graph in Phase 4 
    # (they are huge), we link the user to the graph via their recently watched items.
    graph_path = []
    if recent_items:
        # Try to find a path from a recently watched item to the recommended item
        target_node = f"Movie:{request.item_id}"
        for recent_id in recent_items[:3]: # check top 3 recent items
            start_node = f"Movie:{recent_id}"
            path = graph_engine.find_path(start_node, target_node, max_depth=3)
            if path:
                graph_path = path
                break

    # 4. Generate LLM Explanation
    explanation = llm_provider.generate_explanation(
        user_context=user_context,
        movie_title=title,
        graph_path=graph_path,
        item_id=request.item_id
    )
    
    # 5. Generate Rich Metadata
    rich_metadata = llm_provider.generate_rich_metadata(
        item_id=request.item_id,
        title=title,
        explanation=explanation,
        score=0.0
    )

    return ExplainResponse(
        user_id=request.user_id,
        item_id=request.item_id,
        movie_title=title,
        explanation=explanation,
        graph_path=graph_path,
        rich_metadata=rich_metadata
    )

class ExplainSimilarityRequest(BaseModel):
    source_item_id: int
    target_item_id: int

class ExplainSimilarityResponse(BaseModel):
    source_item_id: int
    target_item_id: int
    target_title: str
    explanation: str
    graph_path: list[str]
    rich_metadata: dict

@app.post("/explain_similarity", response_model=ExplainSimilarityResponse)
def explain_similarity(request: ExplainSimilarityRequest):
    """
    Generates an explanation for why two movies are similar by finding
    the shortest path between them in the Knowledge Graph.
    """
    # 1. Get Target Movie Title
    title = f"Movie {request.target_item_id}"
    if not movies_df.empty:
        row = movies_df[movies_df['item_id'] == request.target_item_id]
        if not row.empty:
            title = row.iloc[0]['title']

    # 2. Find Graph Path directly between the two movies
    source_node = f"Movie:{request.source_item_id}"
    target_node = f"Movie:{request.target_item_id}"
    
    graph_path = graph_engine.find_path(source_node, target_node, max_depth=3)
    if not graph_path:
        graph_path = []

    # 3. Generate LLM Explanation
    # We can reuse the LLM generator, passing the source movie as "user_context"
    source_title = f"Movie {request.source_item_id}"
    if not movies_df.empty:
        s_row = movies_df[movies_df['item_id'] == request.source_item_id]
        if not s_row.empty:
            source_title = s_row.iloc[0]['title']
            
    explanation = llm_provider.generate_explanation(
        user_context=f"the movie '{source_title}'",
        movie_title=title,
        graph_path=graph_path
    )
    
    rich_metadata = llm_provider.generate_rich_metadata(
        item_id=request.target_item_id,
        title=title,
        explanation=explanation,
        score=0.0 # Handled in the metadata gen
    )

    return ExplainSimilarityResponse(
        source_item_id=request.source_item_id,
        target_item_id=request.target_item_id,
        target_title=title,
        explanation=explanation,
        graph_path=graph_path,
        rich_metadata=rich_metadata
    )


@app.get("/")
def health():
    return {
        "status": "STREAMORA AI RAG Service Running",
        "graph_ready": graph_engine.built
    }
