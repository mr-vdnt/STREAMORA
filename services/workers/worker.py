from __future__ import annotations
import logging
from typing import Dict, Callable, Any, Optional
from services.workers.queue import BackgroundTaskQueue, TaskJob
from services.workers.retry import ExponentialBackoffRetry

logger = logging.getLogger("streamora.workers")

class BackgroundWorker:
    """Background worker processing tasks registered in the queue."""

    def __init__(self, task_queue: Optional[BackgroundTaskQueue] = None):
        self.queue = task_queue or BackgroundTaskQueue()
        self.handlers: Dict[str, Callable[[Dict[str, Any]], None]] = {}
        self.retry_engine = ExponentialBackoffRetry()

    def register_handler(self, task_name: str, handler: Callable[[Dict[str, Any]], None]):
        self.handlers[task_name] = handler

    def process_one(self) -> bool:
        job = self.queue.dequeue(timeout=0.1)
        if not job:
            return False

        handler = self.handlers.get(job.name)
        if not handler:
            logger.warning(f"No handler registered for task '{job.name}'")
            self.queue.send_to_dead_letter(job, f"No handler registered for task '{job.name}'")
            return True

        try:
            job.attempts += 1
            self.retry_engine.execute_with_retry(lambda: handler(job.payload), max_attempts=1)
            logger.info(f"Successfully executed worker job '{job.name}' (ID: {job.id})")
        except Exception as e:
            if job.attempts < job.max_retries:
                logger.warning(f"Retrying job '{job.name}' (attempt {job.attempts}/{job.max_retries})")
                self.queue.enqueue(job.name, job.payload, max_retries=job.max_retries)
            else:
                logger.error(f"Job '{job.name}' failed permanently: {str(e)}")
                self.queue.send_to_dead_letter(job, str(e))
        return True
