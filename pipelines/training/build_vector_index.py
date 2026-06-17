import pandas as pd
import numpy as np
import faiss
import os
from sentence_transformers import SentenceTransformer

def build_movie_index():
    # Load data
    movies_path = "data/raw/movies.csv"
    if not os.path.exists(movies_path):
        print(f"{movies_path} not found. Please run mock_data.py first.")
        return

    df = pd.read_csv(movies_path)
    
    # Combine text fields for a rich embedding
    df['text_for_embedding'] = df['title'] + ". " + df['genre'] + ". " + df['description']
    texts = df['text_for_embedding'].tolist()
    
    print("Loading embedding model (all-MiniLM-L6-v2)...")
    # This is a small, fast model ideal for local execution
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print(f"Generating embeddings for {len(texts)} movies...")
    embeddings = model.encode(texts, show_progress_bar=True)
    embeddings = np.array(embeddings).astype('float32')
    
    # Create FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    
    print("Adding embeddings to FAISS index...")
    index.add(embeddings)
    
    # Save the index and metadata
    os.makedirs("data/index", exist_ok=True)
    faiss.write_index(index, "data/index/movies.index")
    df.to_csv("data/index/movies_metadata.csv", index=False)
    
    print("Vector index built and saved to data/index/movies.index")

if __name__ == "__main__":
    build_movie_index()
