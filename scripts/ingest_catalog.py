import os
import sys
import pandas as pd
import numpy as np
import faiss
import json
import re
from sentence_transformers import SentenceTransformer

# Patterns that indicate synthetic/generated content
_SYNTHETIC_TITLE_RE = re.compile(r'\s+\d{2,}$')            # "Title 406", "Whiplash 10"
_SYNTHETIC_OVERVIEW_RE = re.compile(                         # Generated overview template
    r'An extraordinary .+ production|A gripping .+ story that|'
    r'This .+ masterpiece explores|In this .+ tale'
)


def _is_synthetic(row) -> bool:
    """Returns True if a row looks like generated/synthetic content."""
    tmdb_id = int(row.get('tmdb_id', 0))
    # A TMDB ID of 0 or negative means it was never assigned (fabricated)
    if tmdb_id <= 0:
        return True
    title = str(row.get('title', ''))
    suffix_match = re.search(r'\s+(\d+)$', title)
    if suffix_match:
        suffix_num = suffix_match.group(1)
        if not (len(suffix_num) == 4 and (suffix_num.startswith('19') or suffix_num.startswith('20'))):
            return True
    overview = str(row.get('overview', ''))
    if _SYNTHETIC_OVERVIEW_RE.search(overview):
        return True
    return False




def ingest_catalog(csv_path="data/raw/movies.csv", rebuild_all=True):
    print("======================================================================")
    print(" STREAMORA AI - Automated Production Ingestion Pipeline ")
    print("======================================================================")
    
    if not os.path.exists(csv_path):
        print(f"[ERROR] Source catalog {csv_path} not found.")
        sys.exit(1)
        
    df = pd.read_csv(csv_path)
    print(f"[OK] Ingested {len(df)} titles from {csv_path}.")

    # ─────────────────────────────────────────────────────────────────────────
    # PRE-STAGE: Synthetic Content Guard
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[Pre-Stage] Synthetic Content Guard...")
    synthetic_mask = df.apply(_is_synthetic, axis=1)
    synthetic_count = synthetic_mask.sum()
    if synthetic_count > 0:
        print(f"[WARN] Detected {synthetic_count} synthetic/generated entries. Dropping them.")
        for _, bad_row in df[synthetic_mask].iterrows():
            print(f"       Dropped: '{bad_row['title']}' (tmdb_id={bad_row['tmdb_id']})")
        df = df[~synthetic_mask].reset_index(drop=True)
    else:
        print(f"[OK] No synthetic content detected. All {len(df)} entries appear real.")

    # ─────────────────────────────────────────────────────────────────────────
    # STAGE 1: Metadata Validation & Normalization
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[Stage 1/5] Validating & Normalizing Metadata...")
    required_cols = [
        "item_id", "tmdb_id", "title", "genres", "director", "cast",
        "poster_url", "backdrop_url", "language"
    ]
    
    for col in required_cols:
        if col not in df.columns:
            print(f"[ERROR] Missing required column: {col}")
            sys.exit(1)
            
    # Schema validation and cleanup
    df['item_id'] = pd.to_numeric(df['item_id'], errors='coerce').fillna(0).astype(int)
    df['tmdb_id'] = pd.to_numeric(df['tmdb_id'], errors='coerce').fillna(0).astype(int)
    df['rating'] = pd.to_numeric(df.get('rating', 7.5), errors='coerce').fillna(7.5).astype(float)
    df['popularity'] = pd.to_numeric(df.get('popularity', 100.0), errors='coerce').fillna(100.0).astype(float)
    
    # Text normalization — titles kept as-is (no (Year) suffix appended)
    df['title'] = df['title'].astype(str).str.strip()
    df['original_title'] = df.get('original_title', df['title']).astype(str).str.strip()
    df['genres'] = df['genres'].astype(str).str.strip()
    df['director'] = df['director'].astype(str).str.strip()
    df['cast'] = df['cast'].astype(str).str.strip()
    df['language'] = df['language'].astype(str).str.strip()
    
    # Ensure content_type column exists (default: "movie" for backward compatibility)
    if 'content_type' not in df.columns:
        df['content_type'] = 'movie'
    df['content_type'] = df['content_type'].astype(str).str.strip()

    print(f"[OK] Schema validation complete. Total validated items: {len(df)}")

    # ─────────────────────────────────────────────────────────────────────────
    # STAGE 2: Artwork & CDN Validation
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[Stage 2/5] Validating Artwork Domains & CDN Assets...")
    tmdb_url_pattern = re.compile(r'^https://image\.tmdb\.org/t/p/(w500|w1280|original)/.+\.(jpg|png|jpeg)$')
    
    valid_artwork_count = 0
    invalid_artwork_count = 0
    
    valid_indices = []
    for idx, row in df.iterrows():
        poster = str(row['poster_url'])
        backdrop = str(row['backdrop_url'])
        
        # Verify poster and backdrop point to correct official TMDB image host
        if not tmdb_url_pattern.match(poster) or not tmdb_url_pattern.match(backdrop):
            invalid_artwork_count += 1
        else:
            valid_indices.append(idx)
            valid_artwork_count += 1
            
    df = df.loc[valid_indices].reset_index(drop=True)
    df['item_id'] = range(1, len(df) + 1)
            
    print(f"[OK] Artwork validation done: {valid_artwork_count} verified TMDb links, {invalid_artwork_count} invalid items dropped.")

    # ─────────────────────────────────────────────────────────────────────────
    # STAGE 3: FAISS Vector Index Update
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[Stage 3/5] Generating Sentence embeddings & FAISS index...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    texts = []
    for _, row in df.iterrows():
        title = row['title']
        overview = row.get('overview', '')
        genres = str(row['genres']).replace('|', ' ')
        text = f"Title: {title}. Genres: {genres}. Overview: {overview}"
        texts.append(text)
        
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    embeddings = embeddings.astype('float32')
    
    embedding_dim = embeddings.shape[1]
    faiss_index = faiss.IndexFlatIP(embedding_dim)
    faiss_index.add(embeddings)
    
    os.makedirs("data/index", exist_ok=True)
    faiss.write_index(faiss_index, "data/index/semantic_items.index")
    print(f"[OK] FAISS Index rebuilt with {faiss_index.ntotal} vectors in data/index/semantic_items.index")

    # ─────────────────────────────────────────────────────────────────────────
    # STAGE 4: Knowledge Graph CSV Synchronizer
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[Stage 4/5] Aligning and compiling Knowledge Graph CSV tables...")
    actors_map = {}
    directors_map = {}
    actor_id_counter = 1
    director_id_counter = 1
    
    movie_actors_edges = []
    movie_directors_edges = []
    
    for _, row in df.iterrows():
        movie_id = int(row['item_id'])
        
        # 1. Process Directors
        dir_name = str(row['director']).strip()
        if dir_name not in directors_map:
            directors_map[dir_name] = director_id_counter
            director_id_counter += 1
        
        movie_directors_edges.append({
            "movie_id": movie_id,
            "director_id": directors_map[dir_name]
        })
        
        # 2. Process Cast
        cast_list = [c.strip() for c in str(row['cast']).split(',') if c.strip()]
        for actor_name in cast_list:
            if actor_name not in actors_map:
                actors_map[actor_name] = actor_id_counter
                actor_id_counter += 1
                
            movie_actors_edges.append({
                "movie_id": movie_id,
                "actor_id": actors_map[actor_name],
                "role": "Lead Cast"
            })
            
    # Save graph tables
    os.makedirs("data/graph", exist_ok=True)
    actors_df = pd.DataFrame([{"actor_id": aid, "name": name} for name, aid in actors_map.items()])
    directors_df = pd.DataFrame([{"director_id": did, "name": name} for name, did in directors_map.items()])
    ma_df = pd.DataFrame(movie_actors_edges)
    md_df = pd.DataFrame(movie_directors_edges)
    
    actors_df.to_csv("data/graph/actors.csv", index=False)
    directors_df.to_csv("data/graph/directors.csv", index=False)
    ma_df.to_csv("data/graph/movie_actors.csv", index=False)
    md_df.to_csv("data/graph/movie_directors.csv", index=False)
    
    print(f"[OK] Knowledge Graph CSV synced: {len(actors_df)} actors, {len(directors_df)} directors, {len(ma_df)} actor edges, {len(md_df)} director edges.")

    # ─────────────────────────────────────────────────────────────────────────
    # STAGE 5: Pad visual embeddings JSON
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[Stage 5/5] Refreshing and padding visual embeddings JSON...")
    visual_embeddings_path = "data/multimodal/visual_embeddings.json"
    os.makedirs("data/multimodal", exist_ok=True)
    
    existing_embeddings = {}
    if os.path.exists(visual_embeddings_path):
        try:
            with open(visual_embeddings_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        obj = json.loads(line)
                        existing_embeddings[int(obj["item_id"])] = obj["visual_embedding"]
        except Exception:
            pass

    with open(visual_embeddings_path, "w", encoding="utf-8") as f:
        for idx in range(1, len(df) + 1):
            if idx in existing_embeddings:
                emb = existing_embeddings[idx]
            else:
                np.random.seed(idx)
                emb = [round(float(v), 8) for v in np.random.uniform(-0.3, 0.3, size=64)]
            
            line_obj = {"item_id": idx, "visual_embedding": emb}
            f.write(json.dumps(line_obj) + "\n")
            
    print(f"[OK] Visual embeddings updated for {len(df)} movies.")
    
    # Save the normalized movie catalog back to raw storage
    df.to_csv(csv_path, index=False)
    print("\n[SUCCESS] Catalog Ingestion complete. Cache, vector index, and graph mappings synced.")

if __name__ == "__main__":
    ingest_catalog()
