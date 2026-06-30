import os
import sys
import numpy as np
import pandas as pd
import faiss
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

app = FastAPI(title="STREAMORA AI - Multi-Stage Ranking Service")


# ── Request / Response Schemas ──────────────────────────────────────
class RankRequest(BaseModel):
    user_id: int
    top_k_retrieval: int = 50   # How many candidates to pull from FAISS
    top_k_final: int = 10       # How many to return after re-ranking
    exclude_ids: list[int] = []


class RankedItem(BaseModel):
    item_id: int
    title: str
    retrieval_score: float
    ranking_score: float


# ── Global state ────────────────────────────────────────────────────
# DeepFM and PyTorch removed to save 150MB RAM on Render
two_tower = None
deepfm = None
deepfm_optimizer = None
deepfm_loss_fn = None
faiss_index: faiss.Index | None = None
movies_df: pd.DataFrame | None = None
num_users: int = 0
num_items: int = 0


class FeedbackEvent(BaseModel):
    user_id: int
    item_id: int
    label: float  # 1.0 for click/purchase, 0.0 for ignore

@app.on_event("startup")
async def startup_event():
    global two_tower, deepfm, deepfm_optimizer, faiss_index, movies_df, num_users, num_items
    print("Loading models and data …")

    # Load metadata to figure out counts
    ratings = pd.read_csv("data/raw/ratings.csv")
    num_users = int(ratings['user_id'].max())
    num_items = int(ratings['item_id'].max())

    # ── Semantic Search (retrieval) ─────────────────────────────────
    semantic_index_path = "data/index/semantic_items.index"
    if os.path.exists(semantic_index_path):
        faiss_index = faiss.read_index(semantic_index_path)
        print("  [OK] Semantic Content FAISS index loaded")
    else:
        print("  [MISSING] Semantic FAISS index not found - retrieval disabled")

    # ── DeepFM (re-ranking) ─────────────────────────────────────────
    print("  [OK] DeepFM disabled to save 150MB RAM on Render")

    # ── Movie metadata ──────────────────────────────────────────────
    if os.path.exists("data/raw/movies.csv"):
        movies_df = pd.read_csv("data/raw/movies.csv")
        print("  [OK] Movie metadata loaded")


@app.get("/")
def health():
    return {
        "status": "STREAMORA AI Ranking Service Running",
        "retrieval_ready": faiss_index is not None,
        "ranking_ready": deepfm is not None,
    }


class SimilarRequest(BaseModel):
    item_id: int
    top_k: int = 20
    exclude_ids: list[int] = []

@app.post("/similar", response_model=list[RankedItem])
def get_similar_items(request: SimilarRequest):
    """
    Finds mathematically similar movies by searching the 384-D Semantic Space
    via FAISS using Sentence-Transformer embeddings of the plot and genres.
    """
    if faiss_index is None:
        raise HTTPException(status_code=503, detail="Semantic FAISS index not loaded.")
        
    try:
        # FAISS is 0-indexed, our item_ids are 1-based sequential
        idx = request.item_id - 1
        item_emb = faiss_index.reconstruct(idx)
        # Reshape to (1, D)
        item_emb = np.array([item_emb]).astype('float32')
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Could not reconstruct embedding for item {request.item_id}: {e}")

    search_k = request.top_k + len(request.exclude_ids) + 1
    distances, indices = faiss_index.search(item_emb, search_k)
    
    candidate_ids = (indices[0] + 1).tolist()
    retrieval_scores = distances[0].tolist()
    
    results = []
    for cid, r_score in zip(candidate_ids, retrieval_scores):
        if cid == request.item_id or cid in request.exclude_ids:
            continue # Skip the seed movie itself or excluded items
            
        # Confidence Threshold: exclude matches with inner product < 0.40 (low similarity)
        if float(r_score) < 0.40:
            continue
            
        title = ""
        if movies_df is not None:
            row = movies_df[movies_df['item_id'] == cid]
            if not row.empty:
                title = row.iloc[0]['title']
                
        results.append(RankedItem(
            item_id=cid,
            title=title,
            retrieval_score=float(r_score),
            ranking_score=float(r_score) # no deepfm re-ranking for pure similarity yet
        ))
        
        if len(results) == request.top_k:
            break
            
    return results

@app.post("/rank", response_model=list[RankedItem])
def rank(request: RankRequest):
    """
    Full multi-stage pipeline:
      Stage 1 → Two-Tower retrieval via FAISS (fast, 100k→50)
      Stage 2 → DeepFM re-ranking (precise, 50→10)
    """
    if faiss_index is None:
        raise HTTPException(status_code=503, detail="Semantic FAISS retrieval model not loaded.")
    # DeepFM guard removed — we use inverted FAISS distances for ranking now
    if request.user_id < 1 or request.user_id > num_users:
        raise HTTPException(status_code=400, detail=f"user_id must be between 1 and {num_users}")

    # ── Real-Time Features ──────────────────────────────────────────
    user_features = {}
    try:
        resp = requests.get(f"http://127.0.0.1:8002/features/user/{request.user_id}", timeout=1)
        if resp.status_code == 200:
            user_features = resp.json()
    except Exception:
        pass
        
    top_genres = {g[0]: g[1] for g in user_features.get("top_genres", [])}
    recent_items = user_features.get("recent_items", [])

    # ── Stage 1: Retrieval (Content-Based) ──────────────────────────
    candidate_ids = []
    retrieval_scores = []
    
    if len(recent_items) > 0:
        # Get semantic similar items for the user's most recent interaction
        last_item = recent_items[0]
        try:
            item_emb = faiss_index.reconstruct(last_item - 1)
            item_emb = np.array([item_emb]).astype('float32')
            search_k = request.top_k_retrieval + len(request.exclude_ids) + 1
            distances, indices = faiss_index.search(item_emb, search_k)
            candidate_ids = (indices[0] + 1).tolist()
            retrieval_scores = distances[0].tolist()
            
            # Filter exclusions
            filtered_cids = []
            filtered_scores = []
            for c, s in zip(candidate_ids, retrieval_scores):
                if c != last_item and c not in request.exclude_ids:
                    filtered_cids.append(c)
                    filtered_scores.append(s)
            candidate_ids = filtered_cids
            retrieval_scores = filtered_scores
        except Exception:
            candidate_ids = list(range(1, min(request.top_k_retrieval + len(request.exclude_ids) + 1, num_items + 1)))
            candidate_ids = [c for c in candidate_ids if c not in request.exclude_ids]
            retrieval_scores = [1.0] * len(candidate_ids)
    else:
        candidate_ids = list(range(1, min(request.top_k_retrieval + len(request.exclude_ids) + 1, num_items + 1)))
        candidate_ids = [c for c in candidate_ids if c not in request.exclude_ids]
        retrieval_scores = [1.0] * len(candidate_ids)

    # ── Stage 2: Re-ranking with DeepFM ─────────────────────────────
    # DeepFM removed to save RAM on Render. We use inverted FAISS distances.
    rank_scores = [1.0 / (1.0 + d) for d in retrieval_scores]


    # Build results and sort by ranking score (higher = better)
    results = []
    for cid, r_score, rk_score in zip(candidate_ids, retrieval_scores, rank_scores):
        title = ""
        movie_genres = ""
        if movies_df is not None:
            row = movies_df[movies_df['item_id'] == cid]
            if not row.empty:
                title = row.iloc[0]['title']
                if 'genres' in row.columns:
                    movie_genres = row.iloc[0]['genres']
                    
        # Real-time score adjustments
        rt_boost = 0.0
        
        # 1. Genre Boost: if movie matches top real-time genres
        if top_genres and movie_genres:
            for g in movie_genres.split('|'):
                if g in top_genres:
                    rt_boost += top_genres[g] * 0.5  # 50% of the genre score as boost
                    
        # 2. Recent items penalty: don't recommend what they just interacted with
        if cid in recent_items:
            rt_boost -= 10.0
            
        final_score = float(rk_score) + rt_boost

        results.append(RankedItem(
            item_id=cid,
            title=title,
            retrieval_score=float(r_score),
            ranking_score=final_score,
        ))

    results.sort(key=lambda r: r.ranking_score, reverse=True)
    return results[:request.top_k_final]


# ── Online Learning Endpoint ────────────────────────────────────────
@app.post("/feedback")
def process_feedback(event: FeedbackEvent):
    """
    Perform a real-time online learning update (one gradient step)
    on the DeepFM model based on a single user interaction event.
    """
    # Removed PyTorch online learning to save 150MB RAM on Render
    return {
        "status": "success", 
        "updated_weights": False,
        "loss": 0.0
    }
