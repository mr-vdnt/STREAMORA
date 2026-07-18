import logging
import csv
import os
from typing import Dict, Any

from services.platform.cache.cache_manager import CacheManager
from services.platform.monitoring.health import HealthCheck
from services.platform.config.settings import settings
from services.agent.core import OrchestratorAgent

logger = logging.getLogger("streamora.startup")

class Container:
    """Simple Dependency Injection Container."""
    def __init__(self):
        self.movies_db: Dict[int, Any] = {}
        self.cache_manager = CacheManager()
        self.health_check = None
        self.agent = None

container = Container()

def load_catalog():
    if os.path.exists(settings.MOVIES_CSV_PATH):
        with open(settings.MOVIES_CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    iid = int(row.get('item_id', 0))
                    container.movies_db[iid] = row
                except ValueError:
                    pass
        logger.info(f"Loaded {len(container.movies_db)} items into catalog.")

async def startup_event():
    """Initializes global resources."""
    logger.info("Initializing Streamora Platform...")
    
    # 1. Load Data
    load_catalog()
    
    # 2. Setup Health Check
    container.health_check = HealthCheck(container.movies_db, container.cache_manager)
    
    # 3. Setup Orchestrator Agent (Which internally wires Intelligence/Retrieval/Ranking)
    # The OrchestratorAgent in core.py currently loads its own movies_db.
    # In a full DI refactor, we would pass container.movies_db to it.
    container.agent = OrchestratorAgent()
    # Override its DB so they share the same memory instance
    container.agent.movies_db = container.movies_db
    
    logger.info("Streamora Platform initialization complete.")

async def shutdown_event():
    logger.info("Shutting down Streamora Platform...")
    # Clean up caches, close connections
    container.movies_db.clear()
