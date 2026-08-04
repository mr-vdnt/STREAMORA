from __future__ import annotations
import time
from typing import Dict, Any, List, Callable
from services.workers.queue import BackgroundTaskQueue

class BackgroundScheduler:
    """Cron scheduler for periodic background jobs (recommendation refresh, index rebuilding)."""

    def __init__(self, queue: BackgroundTaskQueue):
        self.queue = queue
        self.scheduled_jobs: List[Dict[str, Any]] = []

    def schedule_recurring(self, task_name: str, payload: Dict[str, Any], interval_seconds: float):
        self.scheduled_jobs.append({
            "task_name": task_name,
            "payload": payload,
            "interval_seconds": interval_seconds,
            "last_run": 0.0
        })

    def tick(self) -> int:
        now = time.time()
        triggered = 0
        for job in self.scheduled_jobs:
            if now - job["last_run"] >= job["interval_seconds"]:
                self.queue.enqueue(job["task_name"], job["payload"])
                job["last_run"] = now
                triggered += 1
        return triggered
