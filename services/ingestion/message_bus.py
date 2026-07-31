from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List

from services.ingestion.contracts import MessageType, PipelineMessage, PipelineStage

logger = logging.getLogger("streamora.ingestion.message_bus")


class InProcessMessageBus:
    """In-process message bus for pipeline stage orchestration.

    Routes PipelineMessages to registered stages based on MessageType.
    Designed to be replaced by a distributed message broker (Redis Streams,
    RabbitMQ, Kafka) when horizontal scaling is needed, without changing
    stage implementations.
    """

    def __init__(self):
        self._handlers: Dict[MessageType, List[PipelineStage]] = {}
        self._dead_letter_handler: Callable[[PipelineMessage], Any] | None = None

    def register(self, message_type: MessageType, stage: PipelineStage) -> None:
        """Register a stage to handle a specific message type."""
        if message_type not in self._handlers:
            self._handlers[message_type] = []
        self._handlers[message_type].append(stage)
        logger.info(f"Registered stage '{stage.stage_name}' for {message_type.value}")

    def set_dead_letter_handler(self, handler: Callable[[PipelineMessage], Any]) -> None:
        """Set handler for messages that fail processing."""
        self._dead_letter_handler = handler

    async def publish(self, message: PipelineMessage) -> PipelineMessage | None:
        """Publish a message to all registered handlers for its type.
        
        If a stage outputs a message of a different MessageType, the bus
        automatically routes it to handlers registered for the new type,
        enabling seamless pipeline chaining.
        """
        handlers = self._handlers.get(message.message_type, [])
        if not handlers:
            logger.warning(f"No handlers registered for {message.message_type.value}")
            return message

        current = message
        for stage in handlers:
            try:
                logger.debug(f"Stage '{stage.stage_name}' processing {current.external_id}")
                out_msg = await stage.process(current)
                if out_msg.message_type == MessageType.FAILED:
                    logger.error(f"Stage '{stage.stage_name}' failed for {current.external_id}: {out_msg.error}")
                    if self._dead_letter_handler:
                        self._dead_letter_handler(out_msg)
                    return out_msg

                # If stage transitioned to a new message_type, recursively dispatch to next stage
                if out_msg.message_type != current.message_type:
                    return await self.publish(out_msg)

                current = out_msg
            except Exception as e:
                logger.exception(f"Unhandled error in stage '{stage.stage_name}' for {current.external_id}")
                fail_msg = PipelineMessage(
                    message_type=MessageType.FAILED,
                    job_id=current.job_id,
                    connector_name=current.connector_name,
                    external_id=current.external_id,
                    entity_type=current.entity_type,
                    payload=current.payload,
                    raw_payload_id=current.raw_payload_id,
                    error=f"{stage.stage_name}: {str(e)}",
                    metadata=current.metadata,
                    trace_id=current.trace_id,
                )
                if self._dead_letter_handler:
                    self._dead_letter_handler(fail_msg)
                return fail_msg
        return current
