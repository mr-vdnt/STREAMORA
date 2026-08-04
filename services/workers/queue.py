from __future__ import annotations
import queue
import uuid
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable

@dataclass
class TaskJob:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    attempts: int = 0
    max_retries: int = 3
    created_at: float = field(default_factory=time.time)

class BackgroundTaskQueue:
    """In-memory thread-safe FIFO task queue for background workers."""

    def __init__(self):
        self._q: queue.Queue[TaskJob] = queue.Queue()
        self._dead_letter_queue: list[TaskJob] = []

    def enqueue(self, task_name: str, payload: Dict[str, Any], max_retries: int = 3) -> TaskJob:
        job = TaskJob(name=task_name, payload=payload, max_retries=max_retries)
        self._q.put(job)
        return job

    def dequeue(self, timeout: float = 1.0) -> Optional[TaskJob]:
        try:
            return self._q.get(timeout=timeout)
        except queue.Empty:
            return None

    def send_to_dead_letter(self, job: TaskJob, error: str):
        job.payload["dead_letter_error"] = error
        self._dead_letter_queue.append(job)

    def size(self) -> int:
        return self._q.qsize()

    def dead_letter_size(self) -> int:
        return len(self._dead_letter_queue)
