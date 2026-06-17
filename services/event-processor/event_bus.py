"""
AURORA AI - Event Bus

A lightweight in-process event bus that simulates Kafka-like topic/consumer patterns.
Designed to be swapped out for real Kafka (confluent-kafka) in production.

Architecture:
    Producer -> Topic (asyncio.Queue) -> Consumer Group -> Handler
"""

import asyncio
import json
import time
from collections import defaultdict
from typing import Callable, Any


class EventBus:
    """In-process event bus simulating Kafka topics with consumer groups."""

    def __init__(self):
        self._topics: dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
        self._handlers: dict[str, list[Callable]] = defaultdict(list)
        self._running = False
        self._tasks: list[asyncio.Task] = []
        self._event_count = 0

    async def publish(self, topic: str, event: dict):
        """Publish an event to a topic (analogous to Kafka producer.send)."""
        envelope = {
            "topic": topic,
            "timestamp": time.time(),
            "payload": event,
            "offset": self._event_count,
        }
        self._event_count += 1
        await self._topics[topic].put(envelope)

    def subscribe(self, topic: str, handler: Callable):
        """Register a handler for a topic (analogous to Kafka consumer.subscribe)."""
        self._handlers[topic].append(handler)

    async def _consume(self, topic: str):
        """Background consumer loop for a single topic."""
        queue = self._topics[topic]
        while self._running:
            try:
                envelope = await asyncio.wait_for(queue.get(), timeout=0.5)
                for handler in self._handlers[topic]:
                    try:
                        result = handler(envelope)
                        if asyncio.iscoroutine(result):
                            await result
                    except Exception as e:
                        print(f"[EventBus] Handler error on topic '{topic}': {e}")
            except asyncio.TimeoutError:
                continue

    async def start(self):
        """Start consuming all subscribed topics."""
        self._running = True
        for topic in self._handlers:
            task = asyncio.create_task(self._consume(topic))
            self._tasks.append(task)
        print(f"[EventBus] Started consumers for topics: {list(self._handlers.keys())}")

    async def stop(self):
        """Gracefully stop all consumers."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
        print("[EventBus] Stopped all consumers.")

    @property
    def event_count(self):
        return self._event_count


# Singleton event bus instance
event_bus = EventBus()
