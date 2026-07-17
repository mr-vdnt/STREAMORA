"""
STREAMORA AI - Real-Time Event Processing Service

Unified service that:
  1. Ingests events via REST API (simulating Kafka producer)
  2. Processes events through the Event Bus (simulating Kafka consumer)
  3. Updates real-time user features in the Feature Store (Redis)
  4. Exposes user profiles and system stats

Architecture:
    Client -> POST /events/ingest -> EventBus -> StreamProcessor -> FeatureStore
"""

import os
import sys
import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import using importlib since folder names have hyphens
import importlib
event_bus_mod = importlib.import_module("services.event_processor.event_bus")
feature_store_mod = importlib.import_module("services.feature_store.store")

event_bus = event_bus_mod.event_bus
feature_store = feature_store_mod.feature_store


# ── Schemas ─────────────────────────────────────────────────────────

class EventPayload(BaseModel):
    user_id: int
    item_id: int
    event_type: str  # "view", "click", "purchase"
    genre: str = ""
    device: str = "web"
    session_id: str = ""


class BatchEventPayload(BaseModel):
    events: list[EventPayload]


# ── Stream Processor (Kafka Consumer analogue) ──────────────────────

class StreamProcessor:
    """
    Consumes events from the event bus and updates the feature store.
    In production, this would be a Flink/Spark Streaming job.
    """

    def __init__(self):
        self.processed_count = 0

    def process_event(self, envelope: dict):
        """Handle a single event from the bus."""
        payload = envelope["payload"]
        metadata = {
            "genre": payload.get("genre", ""),
            "device": payload.get("device", "web"),
            "session_id": payload.get("session_id", ""),
        }
        feature_store.record_event(
            user_id=payload["user_id"],
            event_type=payload["event_type"],
            item_id=payload["item_id"],
            metadata=metadata,
        )
        self.processed_count += 1


stream_processor = StreamProcessor()


# ── App Lifecycle ───────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Subscribe the stream processor to event topics
    event_bus.subscribe("user_events", stream_processor.process_event)
    await event_bus.start()
    print("[EventProcessor] Stream processor started. Listening for events...")
    load_visual_embeddings()
    yield
    await event_bus.stop()
    print("[EventProcessor] Shut down.")


app = FastAPI(title="STREAMORA AI - Real-Time Event Processing Service", lifespan=lifespan)


# ── Event Ingestion Endpoints ───────────────────────────────────────

@app.post("/events/ingest")
async def ingest_event(event: EventPayload):
    """
    Ingest a single user event.
    Analogous to a Kafka producer publishing to a topic.
    """
    await event_bus.publish("user_events", event.model_dump())
    return {"status": "accepted", "offset": event_bus.event_count - 1}


@app.post("/events/batch")
async def ingest_batch(batch: BatchEventPayload):
    """Ingest a batch of events at once."""
    for event in batch.events:
        await event_bus.publish("user_events", event.model_dump())
    return {"status": "accepted", "count": len(batch.events)}


# ── Feature Store Read Endpoints ────────────────────────────────────

@app.get("/features/user/{user_id}")
def get_user_features(user_id: int):
    """Get real-time feature profile for a user."""
    profile = feature_store.get_user_profile(user_id)
    if not profile["exists"]:
        raise HTTPException(status_code=404, detail=f"No features found for user {user_id}")
    profile["recent_items"] = feature_store.get_recent_items(user_id, limit=10)
    profile["top_genres"] = feature_store.get_top_genres(user_id, top_k=5)
    return profile

@app.get("/features/global")
def get_global_features():
    """Get global trending items."""
    trending = feature_store.get_global_trending(top_k=20)
    # If no trending data yet (e.g., fresh start without event simulator), return fallback from movies.csv sorted by popularity
    if not trending:
        try:
            import pandas as pd
            if os.path.exists("data/raw/movies.csv"):
                df = pd.read_csv("data/raw/movies.csv")
                top_pops = df.sort_values(by='popularity', ascending=False).head(20)
                trending = [(int(row['item_id']), float(row['popularity'])) for _, row in top_pops.iterrows()]
        except Exception as e:
            print(f"Error loading trending fallback: {e}")
    if not trending:
        trending = [(1, 5.0), (2, 4.5), (3, 4.0), (4, 3.5), (5, 3.0)]
    return {"popular_items": trending}

# ── Multimodal Feature Endpoints ────────────────────────────────────
visual_embeddings_cache = {}

def load_visual_embeddings():
    path = "data/multimodal/visual_embeddings.json"
    if os.path.exists(path):
        import pandas as pd
        df = pd.read_json(path, lines=True)
        for _, row in df.iterrows():
            visual_embeddings_cache[int(row["item_id"])] = row["visual_embedding"]
        print(f"[FeatureStore] Loaded {len(visual_embeddings_cache)} visual embeddings.")

@app.get("/features/visual/{item_id}")
def get_visual_features(item_id: int):
    """Get the visual embedding vector for a movie."""
    if item_id in visual_embeddings_cache:
        return {"item_id": item_id, "visual_embedding": visual_embeddings_cache[item_id]}
    raise HTTPException(status_code=404, detail="Visual embedding not found")

# ── System Endpoints ────────────────────────────────────────────────
@app.get("/")
def health():
    return {
        "status": "STREAMORA AI Event Processing Service Running",
        "events_published": event_bus.event_count,
        "events_processed": stream_processor.processed_count,
        "feature_store": feature_store.get_stats(),
    }


@app.get("/stats")
def system_stats():
    return {
        "event_bus": {
            "total_published": event_bus.event_count,
            "topics": list(event_bus._handlers.keys()),
        },
        "stream_processor": {
            "total_processed": stream_processor.processed_count,
        },
        "feature_store": feature_store.get_stats(),
    }
