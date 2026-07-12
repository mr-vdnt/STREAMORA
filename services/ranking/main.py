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
    explanation: list[str] = []


# ── Global state ────────────────────────────────────────────────────
# DeepFM and PyTorch removed to save 150MB RAM on Render
two_tower = None
deepfm = None
deepfm_optimizer = None
deepfm_loss_fn = None
faiss_index: faiss.Index | None = None
faiss_id_mapping: list[int] = []
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
    global two_tower, deepfm, deepfm_optimizer, faiss_index, faiss_id_mapping, movies_df, num_users, num_items, model
    print("Loading models and data …")

    # Load metadata to figure out counts
    ratings = pd.read_csv("data/raw/ratings.csv")
    num_users = int(ratings['user_id'].max())
    num_items = int(ratings['item_id'].max())

    # ── Semantic Search (retrieval) ─────────────────────────────────
    semantic_index_path = "data/index/semantic_items.index"
    mapping_path = "data/index/semantic_items_mapping.json"
    if os.path.exists(semantic_index_path):
        faiss_index = faiss.read_index(semantic_index_path)
        print("  [OK] Semantic Content FAISS index loaded")
        if os.path.exists(mapping_path):
            import json
            with open(mapping_path, "r") as f:
                global faiss_id_mapping
                faiss_id_mapping = json.load(f)
            print("  [OK] Semantic ID mapping loaded")
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
    target_genres: list[str] = []
    target_moods: list[str] = []
    target_actors: list[str] = []
    target_director: str = ""
    target_content_type: str = ""
    top_k: int = 20
    exclude_ids: list[int] = []

@app.post("/search", response_model=list[RankedItem])
def search_semantic(request: SearchRequest):
    try:
        # Phase 2: Search Modes - Exact Match Check First
        exact_matches = []
        if movies_df is not None and len(request.query) > 2:
            query_lower = request.query.lower().strip()
            # Simple Exact/Fuzzy Title Match
            exact_rows = movies_df[movies_df['title'].str.lower() == query_lower]
            if exact_rows.empty:
                exact_rows = movies_df[movies_df['title'].str.lower().str.contains(query_lower, regex=False)]
            # If still empty and FAISS is down, fallback to overview
            if exact_rows.empty and (faiss_index is None or model is None):
                exact_rows = movies_df[movies_df['overview'].fillna('').str.lower().str.contains(query_lower, regex=False)]
                
            for _, row in exact_rows.iterrows():
                exact_matches.append(int(row['item_id']))
                
        candidate_ids = []
        retrieval_scores = []
        
        # Merge exact matches into candidates to ensure they get scored
        for ex_id in exact_matches:
            if ex_id not in request.exclude_ids:
                candidate_ids.append(ex_id)
                retrieval_scores.append(0.0) # Dist 0 for perfect match
                
        # Phase 2: Semantic Search (FAISS)
        if faiss_index is not None and model is not None:
            query_emb = model.encode([request.query], convert_to_numpy=True).astype('float32')
            search_k = 150  # Pull large candidate pool for robust re-ranking
            distances, indices = faiss_index.search(query_emb, search_k)
            
            for idx_pos, idx in enumerate(indices[0]):
                if idx >= 0 and idx < len(faiss_id_mapping):
                    cid = faiss_id_mapping[idx]
                else:
                    cid = int(idx + 1)
                    
                if cid not in candidate_ids and cid not in request.exclude_ids:
                    candidate_ids.append(cid)
                    retrieval_scores.append(float(distances[0][idx_pos]))
                
        results = []
        for cid, r_score in zip(candidate_ids, retrieval_scores):
            if movies_df is None: continue
            row = movies_df[movies_df['item_id'] == cid]
            if row.empty: continue
            cand = row.iloc[0]
            
            # --- Phase 3: Strict Metadata Validation & Filtering ---
            c_type = str(cand.get('content_type', '')).lower()
            if request.target_content_type:
                # E.g. 'series' in request must match 'series' in db
                if request.target_content_type == "series" and "series" not in c_type: continue
                if request.target_content_type == "movie" and "movie" not in c_type: continue
            
            c_genres = [g.strip().lower() for g in str(cand.get('genres', '')).split('|')]
            c_moods = [m.strip().lower() for m in str(cand.get('moods', '')).split('|')]
            c_themes = [t.strip().lower() for t in str(cand.get('themes', '')).split('|')]
            c_cast = [a.strip().lower() for a in str(cand.get('cast', '')).split(',')]
            c_director = str(cand.get('director', '')).lower()
            c_title = str(cand.get('title', ''))
            c_poster = str(cand.get('poster_url', ''))
            if not c_title or c_poster == 'nan' or not c_poster: continue
            c_rating = float(cand.get('rating', 7.0))
            
            # --- Phase 4: Hybrid Ranking Formula ---
            # Score Components
            semantic_score = max(0.0, 1.0 - (r_score / 2.0)) # Invert FAISS L2 distance (approximate)
            if cid in exact_matches: semantic_score = 1.0
                
            genre_overlap = 0.0
            if request.target_genres:
                req_g = set([g.lower() for g in request.target_genres])
                overlap = req_g.intersection(set(c_genres))
                if not overlap and request.target_genres and semantic_score < 0.6: continue # Strict validation drop
                genre_overlap = len(overlap) / len(req_g) if req_g else 0.0
                
            mood_theme_match = 0.0
            if request.target_moods:
                req_m = set([m.lower() for m in request.target_moods])
                m_overlap = req_m.intersection(set(c_moods + c_themes))
                mood_theme_match = len(m_overlap) / len(req_m) if req_m else 0.0
                
            # Phase 5: Knowledge Graph Proximity (Actors/Directors)
            kg_proximity = 0.0
            if request.target_actors:
                req_a = set([a.lower() for a in request.target_actors])
                a_overlap = req_a.intersection(set(c_cast))
                if not a_overlap and request.target_actors and semantic_score < 0.6: continue # Strict drop
                kg_proximity += 0.5 * (len(a_overlap) / len(req_a))
                
            if request.target_director:
                if request.target_director.lower() in c_director:
                    kg_proximity += 0.5
                elif semantic_score < 0.6:
                    continue # Strict drop
                    
            popularity_score = c_rating / 10.0
            
            # Netflix-style Formula
            final_score = (0.40 * semantic_score) + (0.20 * genre_overlap) + (0.15 * kg_proximity) + (0.15 * mood_theme_match) + (0.10 * popularity_score)
            
            # --- Phase 6: Explainability ---
            explanations = []
            if cid in exact_matches:
                explanations.append("Exact title match")
            else:
                if genre_overlap > 0: explanations.append(f"Matches requested genres ({', '.join(request.target_genres)})")
                if mood_theme_match > 0: explanations.append(f"Matches requested mood/theme ({', '.join(request.target_moods)})")
                if kg_proximity > 0: explanations.append(f"Graph Connection (Cast/Director)")
                if semantic_score > 0.7: explanations.append("Strong semantic plot similarity")
                if popularity_score > 0.8: explanations.append("Critically acclaimed globally")
                
            results.append(RankedItem(
                item_id=cid,
                title=c_title,
                retrieval_score=r_score,
                ranking_score=final_score,
                explanation=explanations
            ))
            
        results.sort(key=lambda r: r.ranking_score, reverse=True)
        return results[:request.top_k]
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
        idx = -1
        if faiss_id_mapping and request.item_id in faiss_id_mapping:
            idx = faiss_id_mapping.index(request.item_id)
        else:
            idx = request.item_id - 1
            
        if idx < 0:
            raise HTTPException(status_code=404, detail="Item ID not found in FAISS mapping")
            
        item_emb = faiss_index.reconstruct(idx)
        # Reshape to (1, D)
        item_emb = np.array([item_emb]).astype('float32')
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Could not reconstruct embedding for item {request.item_id}: {e}")

    search_k = request.top_k + len(request.exclude_ids) + 1
    distances, indices = faiss_index.search(item_emb, search_k)
    
    candidate_ids = []
    for idx in indices[0]:
        if idx >= 0 and idx < len(faiss_id_mapping):
            candidate_ids.append(faiss_id_mapping[idx])
        else:
            candidate_ids.append(int(idx + 1))
    retrieval_scores = distances[0].tolist()
    
    # ── Fetch Seed Metadata for Hybrid Filtering ──
    seed_content_type = "movie"
    seed_genres = set()
    seed_director = ""
    if movies_df is not None:
        seed_row = movies_df[movies_df['item_id'] == request.item_id]
        if not seed_row.empty:
            seed_content_type = seed_row.iloc[0].get('content_type', 'movie')
            seed_genres = set(str(seed_row.iloc[0].get('genres', '')).split('|'))
            seed_director = str(seed_row.iloc[0].get('director', ''))

    results = []
    for cid, r_score in zip(candidate_ids, retrieval_scores):
        if cid == request.item_id or cid in request.exclude_ids:
            continue # Skip the seed movie itself or excluded items
            
        # Confidence Threshold: strict threshold for semantic similarity
        if float(r_score) < 0.50:
            continue
            
        title = ""
        explanation_list = []
        if movies_df is not None:
            row = movies_df[movies_df['item_id'] == cid]
            if not row.empty:
                cand = row.iloc[0]
                
                # STRICT FILTERING 1: Content Type Match
                if cand.get('content_type', 'movie') != seed_content_type:
                    continue
                    
                # STRICT FILTERING 2: Genre Overlap
                cand_genres = set(str(cand.get('genres', '')).split('|'))
                overlap = seed_genres.intersection(cand_genres)
                if not overlap:
                    continue
                    
                title = cand['title']
                
                # DYNAMIC EXPLANATION GENERATION
                if seed_director and cand.get('director') == seed_director:
                    explanation_list.append("Same director")
                
                if overlap:
                    explanation_list.append(" + ".join(list(overlap)[:3]))
                    
                if float(r_score) > 0.70:
                    explanation_list.append("Strong semantic similarity")
                
        results.append(RankedItem(
            item_id=cid,
            title=title,
            retrieval_score=float(r_score),
            ranking_score=float(r_score), # no deepfm re-ranking for pure similarity yet
            explanation=explanation_list
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
