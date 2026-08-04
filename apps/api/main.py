from __future__ import annotations
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from services.api.v2_router import v2_router
from services.observability.metrics_exporter import PrometheusMetricsExporter

app = FastAPI(
    title="Streamora Streaming & Intelligence Platform",
    version="1.1.0-production",
    description="Enterprise AI-Powered Streaming Platform"
)

# Enable CORS for cross-origin frontend support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount v2 Router
app.include_router(v2_router)

exporter = PrometheusMetricsExporter()

@app.get("/health/live")
def health_live():
    return {"status": "ALIVE", "version": "1.1.0-production"}

@app.get("/health/ready")
def health_ready():
    return exporter.get_health_status()

# Mount frontend static files if directory exists
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend"))
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
