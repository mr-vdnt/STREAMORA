from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import os

app = FastAPI(title="AURORA AI - Recommendation Service (MVP)")

class QueryRequest(BaseModel):
    query: str
    top_k: int = 3

class RecommendationResponse(BaseModel):
    id: int
    title: str
    genre: str
    description: str
    score: float

# Global variables to hold model, index, and metadata
model = None
index = None
metadata = None

@app.on_event("startup")
async def startup_event():
    global model, index, metadata
    print("Loading models and data...")
    
    # Load SentenceTransformer
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
    except Exception as e:
        print(f"Error loading model: {e}")
        
    # Load FAISS index
    # We will run this from the root directory or adjust path accordingly
    index_path = "data/index/movies.index"
    if os.path.exists(index_path):
        index = faiss.read_index(index_path)
    else:
        print(f"Warning: Index not found at {index_path}")
        
    # Load metadata
    meta_path = "data/index/movies_metadata.csv"
    if os.path.exists(meta_path):
        metadata = pd.read_csv(meta_path)
    else:
        print(f"Warning: Metadata not found at {meta_path}")

@app.get("/")
def read_root():
    return {"status": "AURORA AI Recommendation Service Running"}

@app.post("/recommend", response_model=list[RecommendationResponse])
def recommend(request: QueryRequest):
    if index is None or metadata is None or model is None:
        raise HTTPException(status_code=500, detail="Service not fully initialized (missing index, model, or metadata).")
    
    # Generate embedding for the query
    query_emb = model.encode([request.query])
    query_emb = np.array(query_emb).astype('float32')
    
    # Perform search
    distances, indices = index.search(query_emb, request.top_k)
    
    results = []
    for i, idx in enumerate(indices[0]):
        if idx == -1: # FAISS returns -1 if there are not enough items
            continue
            
        movie_row = metadata.iloc[idx]
        results.append(RecommendationResponse(
            id=int(movie_row['id']),
            title=movie_row['title'],
            genre=movie_row['genre'],
            description=movie_row['description'],
            score=float(distances[0][i])
        ))
        
    return results
