import os
import pandas as pd
import numpy as np
import faiss
import torch
from sentence_transformers import SentenceTransformer

def build_index():
    if not os.path.exists("data/raw/movies.csv"):
        print("movies.csv not found!")
        return

    df = pd.read_csv("data/raw/movies.csv")
    print(f"Loaded {len(df)} movies for semantic embedding...")

    print("Loading SentenceTransformer model (all-MiniLM-L6-v2)...")
    # Small, fast model perfect for sentence/paragraph embeddings
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Prepare text for embedding: combine title, genres, and overview
    texts = []
    for _, row in df.iterrows():
        title = row.get('title', '')
        overview = row.get('overview', '')
        genres = str(row.get('genres', '')).replace('|', ' ')
        
        # Netflix-style semantic text: Title + Genres + Plot
        text = f"Title: {title}. Genres: {genres}. Overview: {overview}"
        texts.append(text)

    print("Generating embeddings (this may take a minute)...")
    # Output is a NumPy array of shape (N, 384)
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    embeddings = embeddings.astype('float32')

    print("Building FAISS index...")
    embedding_dim = embeddings.shape[1]
    
    # We use IndexFlatIP (Inner Product) which is equivalent to Cosine Similarity 
    # since sentence-transformers outputs normalized embeddings.
    faiss_index = faiss.IndexFlatIP(embedding_dim)
    
    # Add embeddings to the index. Note: FAISS is 0-indexed. 
    # The IDs will correspond to the dataframe index.
    faiss_index.add(embeddings)

    # Create mapping from FAISS index to item_id
    id_mapping = df['item_id'].tolist()
    
    import json
    os.makedirs("data/index", exist_ok=True)
    faiss.write_index(faiss_index, "data/index/semantic_items.index")
    
    with open("data/index/semantic_items_mapping.json", "w") as f:
        json.dump(id_mapping, f)
        
    print(f"Successfully saved Semantic FAISS index with {faiss_index.ntotal} vectors and mapping to data/index/!")

if __name__ == "__main__":
    build_index()
