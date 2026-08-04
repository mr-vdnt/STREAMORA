from __future__ import annotations
import logging
from typing import Dict, List, Callable, Any
from services.events.event_registry import EventTopic

logger = logging.getLogger("streamora.events")

class EventBus:
    """Decoupled in-process publish-subscribe Event Bus."""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}

    def subscribe(self, topic: EventTopic | str, handler: Callable[[Dict[str, Any]], None]):
        topic_name = topic.value if isinstance(topic, EventTopic) else topic
        if topic_name not in self._subscribers:
            self._subscribers[topic_name] = []
        self._subscribers[topic_name].append(handler)

    def publish(self, topic: EventTopic | str, payload: Dict[str, Any]):
        topic_name = topic.value if isinstance(topic, EventTopic) else topic
        handlers = self._subscribers.get(topic_name, [])
        for handler in handlers:
            try:
                handler(payload)
            except Exception as e:
                logger.exception(f"Error executing event handler for topic '{topic_name}': {str(e)}")
