import os
from fastapi import FastAPI
import uvicorn

# Import the FastAPI apps from each microservice
from services.ranking.main import app as ranking_app
from services.rag.main import app as rag_app
from services.event_processor.main import app as event_app
from services.agent.main import app as agent_app

app = FastAPI(title="Streamora AI - Modular Monolith")

# Mount microservices
app.mount("/ranking", ranking_app)
app.mount("/rag", rag_app)
app.mount("/event", event_app)
# Agent app handles the frontend, auth, and orchestration, so mount at root
app.mount("/", agent_app)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
