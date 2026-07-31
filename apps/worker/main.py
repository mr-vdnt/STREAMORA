"""
Streamora Celery Worker Entrypoint
Executes metadata sync, recommendation pre-computation, cache warming, and cleanup jobs.
"""
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("streamora-worker")

def run_worker():
    logger.info("Initializing Streamora Async Celery Worker...")
    logger.info("Worker ready to accept background jobs: [metadata_sync, cache_warming, recommendation_precompute]")

if __name__ == "__main__":
    run_worker()
