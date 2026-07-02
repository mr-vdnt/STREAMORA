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
model = None


class FeedbackEvent(BaseModel):
    user_id: int
    item_id: int
    label: float  # 1.0 for click/purchase, 0.0 for ignore

@app.on_event("startup")
async def startup_event():
    global two_tower, deepfm, deepfm_optimizer, faiss_index, movies_df, num_users, num_items, model
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

    # ── SentenceTransformer ─────────────────────────────────────────
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("  [OK] SentenceTransformer model loaded")
    except Exception as e:
        print(f"  [ERROR] Failed to load SentenceTransformer: {e}")

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


class SearchRequest(BaseModel):
    query: str
    top_k: int = 20
    exclude_ids: list[int] = []


@app.post("/search", response_model=list[RankedItem])
def search_semantic(request: SearchRequest):
    if faiss_index is None or model is None:
        raise HTTPException(status_code=503, detail="Semantic Search models not ready.")
    
    try:
        # Encode query
        query_emb = model.encode([request.query], convert_to_numpy=True)
        query_emb = query_emb.astype('float32')
        
        # Search FAISS index
        search_k = request.top_k + len(request.exclude_ids)
        distances, indices = faiss_index.search(query_emb, search_k)
        
        candidate_ids = (indices[0] + 1).tolist()
        retrieval_scores = distances[0].tolist()
        
        results = []
        for cid, r_score in zip(candidate_ids, retrieval_scores):
            if cid in request.exclude_ids:
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
                ranking_score=float(r_score)
            ))
            
            if len(results) == request.top_k:
                break
                
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        c_director = ""
        c_cast = set()
        c_writer = ""
        c_themes = set()
        c_moods = set()
        c_studio = ""
        c_lang = ""
        c_country = ""
        c_franchise = "None"
        c_year = 2022
        import re

        if movies_df is not None:
            row = movies_df[movies_df['item_id'] == cid]
            if not row.empty:
                r_data = row.iloc[0]
                title = r_data.get('title', '')
                movie_genres = r_data.get('genres', '')
                c_director = str(r_data.get('director', ''))
                c_cast = set(str(r_data.get('cast', '')).split(', '))
                c_writer = str(r_data.get('writer', ''))
                c_themes = set(str(r_data.get('themes', '')).split('|'))
                c_moods = set(str(r_data.get('moods', '')).split('|'))
                c_studio = str(r_data.get('studio', ''))
                c_lang = str(r_data.get('language', ''))
                c_country = str(r_data.get('countries', ''))
                c_franchise = str(r_data.get('franchise', 'None'))
                
                # Extract year from title
                year_match = re.search(r'\((\d{4})\)', title)
                if year_match:
                    c_year = int(year_match.group(1))
                    
        # Real-time score adjustments
        rt_boost = 0.0
        
        # 1. Genre Boost: if movie matches top real-time genres
        if top_genres and movie_genres:
            for g in movie_genres.split('|'):
                if g in top_genres:
                    rt_boost += top_genres[g] * 0.5  # 50% of the genre score as boost
                    
        # 2. Advanced Multi-Signal Overlaps with user's recently watched items
        if recent_items and movies_df is not None:
            # Look up top 5 recent items metadata
            recent_rows = movies_df[movies_df['item_id'].isin(recent_items[:5])]
            for _, r_rec in recent_rows.iterrows():
                # Director overlap
                if c_director and c_director == r_rec.get('director', ''):
                    rt_boost += 1.5
                # Writer overlap
                if c_writer and c_writer == r_rec.get('writer', ''):
                    rt_boost += 1.0
                # Studio overlap
                if c_studio and c_studio == r_rec.get('studio', ''):
                    rt_boost += 0.8
                # Language similarity
                if c_lang and c_lang == r_rec.get('language', ''):
                    rt_boost += 0.5
                # Country similarity
                if c_country and c_country == r_rec.get('countries', ''):
                    rt_boost += 0.5
                # Era / Year similarity (within 5 years)
                try:
                    r_rec_title = r_rec.get('title', '')
                    r_year_match = re.search(r'\((\d{4})\)', r_rec_title)
                    r_year = int(r_year_match.group(1)) if r_year_match else 2022
                    if abs(c_year - r_year) <= 5:
                        rt_boost += 0.3
                except Exception:
                    pass
                # Cast overlap
                r_cast = set(str(r_rec.get('cast', '')).split(', '))
                cast_intersect = c_cast.intersection(r_cast)
                if cast_intersect:
                    rt_boost += len(cast_intersect) * 0.6
                # Themes overlap
                r_themes = set(str(r_rec.get('themes', '')).split('|'))
                theme_intersect = c_themes.intersection(r_themes)
                if theme_intersect:
                    rt_boost += len(theme_intersect) * 0.8
                # Moods overlap
                r_moods = set(str(r_rec.get('moods', '')).split('|'))
                mood_intersect = c_moods.intersection(r_moods)
                if mood_intersect:
                    rt_boost += len(mood_intersect) * 0.8
                # Franchise overlap
                if c_franchise != 'None' and c_franchise == r_rec.get('franchise', ''):
                    rt_boost += 2.0
                    
        # 3. Recent items penalty: don't recommend what they just interacted with
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
