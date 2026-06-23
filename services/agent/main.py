"""
AURORA AI - Orchestrator Agent API

Provides the unified natural language interface for the entire platform.
"""
import os
import sys
from typing import Any
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import mimetypes

mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from services.agent.core import agent

app = FastAPI(title="AURORA AI - Orchestrator Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    user_id: int
    query: str

class ChatResponse(BaseModel):
    intent: str
    response: Any

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    result = agent.process_query(req.user_id, req.query)
    return ChatResponse(
        intent=result["intent"],
        response=result["response"]
    )

import pandas as pd
@app.get("/autocomplete")
def autocomplete(q: str):
    """Real-time autocomplete endpoint matching movie titles."""
    if len(q) < 2:
        return []
    try:
        if os.path.exists("data/raw/movies.csv"):
            df = pd.read_csv("data/raw/movies.csv")
            # Return top 5 exact/prefix or substring matches
            matches = df[df['title'].str.contains(q, case=False, na=False)].head(5)
            titles = matches['title'].tolist()
            # Clean up trailing year "(1995)" for cleaner search
            titles = [t.split(" (")[0] for t in titles]
            return titles
    except Exception as e:
        print("Autocomplete error:", e)
    return []

# Mount frontend directory at root
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../frontend'))
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
