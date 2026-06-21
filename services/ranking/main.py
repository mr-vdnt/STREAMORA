import os
import sys
import torch
import numpy as np
import pandas as pd
import faiss
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from models.collaborative.two_tower import TwoTowerModel
from models.rerankers.deepfm import DeepFM

app = FastAPI(title="AURORA AI - Multi-Stage Ranking Service")


# ── Request / Response Schemas ──────────────────────────────────────
class RankRequest(BaseModel):
    user_id: int
    top_k_retrieval: int = 50   # How many candidates to pull from FAISS
    top_k_final: int = 10       # How many to return after re-ranking


class RankedItem(BaseModel):
    item_id: int
    title: str
    retrieval_score: float
    ranking_score: float


# ── Global state ────────────────────────────────────────────────────
two_tower: TwoTowerModel | None = None
deepfm: DeepFM | None = None
deepfm_optimizer: torch.optim.Optimizer | None = None
deepfm_loss_fn = torch.nn.BCEWithLogitsLoss()
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
    dfm_weights = "models/rerankers/deepfm_weights.pth"
    if os.path.exists(dfm_weights):
        deepfm = DeepFM(num_users=num_users, num_items=num_items, embedding_dim=32, hidden_dims=[64, 32], visual_dim=64)
        deepfm.load_state_dict(torch.load(dfm_weights, map_location="cpu", weights_only=True))
        deepfm.eval()
        
        # Initialize Optimizer for Online Learning
        deepfm_optimizer = torch.optim.Adam(deepfm.parameters(), lr=0.005)
        print("  [OK] DeepFM ranker loaded with Online Learning Optimizer")
    else:
        print("  [MISSING] DeepFM weights not found - ranking disabled")

    # ── Movie metadata ──────────────────────────────────────────────
    if os.path.exists("data/raw/movies.csv"):
        movies_df = pd.read_csv("data/raw/movies.csv")
        print("  [OK] Movie metadata loaded")


@app.get("/")
def health():
    return {
        "status": "AURORA AI Ranking Service Running",
        "retrieval_ready": faiss_index is not None,
        "ranking_ready": deepfm is not None,
    }


class SimilarRequest(BaseModel):
    item_id: int
    top_k: int = 20

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

    # We ask for top_k + 1 because the most similar item to X is X itself.
    distances, indices = faiss_index.search(item_emb, request.top_k + 1)
    
    candidate_ids = (indices[0] + 1).tolist()
    retrieval_scores = distances[0].tolist()
    
    results = []
    for cid, r_score in zip(candidate_ids, retrieval_scores):
        if cid == request.item_id:
            continue # Skip the seed movie itself
            
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
    if deepfm is None:
        raise HTTPException(status_code=503, detail="DeepFM ranking model not loaded.")
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
            distances, indices = faiss_index.search(item_emb, request.top_k_retrieval + 1)
            candidate_ids = (indices[0] + 1).tolist()
            retrieval_scores = distances[0].tolist()
            # Remove the seed item
            if last_item in candidate_ids:
                idx = candidate_ids.index(last_item)
                candidate_ids.pop(idx)
                retrieval_scores.pop(idx)
        except Exception:
            # Fallback to popular items if reconstruction fails
            candidate_ids = list(range(1, min(request.top_k_retrieval + 1, num_items + 1)))
            retrieval_scores = [1.0] * len(candidate_ids)
    else:
        # Fallback to general popular items (e.g. first N items, assuming sorted by popularity)
        candidate_ids = list(range(1, min(request.top_k_retrieval + 1, num_items + 1)))
        retrieval_scores = [1.0] * len(candidate_ids)

    # ── Stage 2: Re-ranking with DeepFM ─────────────────────────────
    with torch.no_grad():
        u_tensor = torch.tensor([request.user_id] * len(candidate_ids), dtype=torch.long)
        i_tensor = torch.tensor(candidate_ids, dtype=torch.long)
        
        # Fetch Multimodal Visual Features for candidates
        visual_features = []
        for cid in candidate_ids:
            try:
                resp = requests.get(f"http://127.0.0.1:8002/features/visual/{cid}", timeout=0.5)
                if resp.status_code == 200:
                    visual_features.append(resp.json()["visual_embedding"])
                else:
                    visual_features.append([0.0] * 64)
            except Exception:
                visual_features.append([0.0] * 64)
                
        v_tensor = torch.tensor(visual_features, dtype=torch.float32)
        rank_scores = deepfm(u_tensor, i_tensor, v_tensor).numpy().tolist()


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
    if deepfm is None or deepfm_optimizer is None:
        raise HTTPException(status_code=503, detail="Model or Optimizer not loaded.")
        
    deepfm.train() # Switch to training mode
    deepfm_optimizer.zero_grad()
    
    u_tensor = torch.tensor([event.user_id], dtype=torch.long)
    i_tensor = torch.tensor([event.item_id], dtype=torch.long)
    
    # Fetch Visual Embedding
    try:
        resp = requests.get(f"http://127.0.0.1:8002/features/visual/{event.item_id}", timeout=0.5)
        if resp.status_code == 200:
            v_vec = resp.json()["visual_embedding"]
            v_tensor = torch.tensor([v_vec], dtype=torch.float32)
        else:
            v_tensor = torch.zeros(1, 64)
    except Exception:
        v_tensor = torch.zeros(1, 64)
        
    # Forward Pass
    pred = deepfm(u_tensor, i_tensor, v_tensor)
    
    # Calculate BCE Loss
    target = torch.tensor([event.label], dtype=torch.float32)
    loss = deepfm_loss_fn(pred, target)
    
    # Backward Pass & Optimize!
    loss.backward()
    deepfm_optimizer.step()
    
    deepfm.eval() # Switch back to eval mode
    
    return {
        "status": "success", 
        "updated_weights": True,
        "loss": float(loss.item())
    }
