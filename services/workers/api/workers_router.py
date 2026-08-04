from fastapi import APIRouter
from services.workers.queue import BackgroundTaskQueue

workers_router = APIRouter(prefix="/workers", tags=["Background Worker Platform"])
queue = BackgroundTaskQueue()

@workers_router.get("/status")
def get_worker_status():
    return {
        "status": "HEALTHY",
        "pending_jobs": queue.size(),
        "dead_letter_jobs": queue.dead_letter_size()
    }
