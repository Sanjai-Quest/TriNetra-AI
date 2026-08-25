"""
RabbitMQ message bus wrapper for TriNetra Phase 2.
Provides async publish and synchronous consume (via aio-pika) for all services.
"""

import asyncio
import json
import logging
import os
from typing import Any, Callable, Dict, Optional

import aio_pika
from aio_pika import connect_robust, Message, DeliveryMode
from aio_pika.abc import AbstractIncomingMessage

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv(
    "RABBITMQ_URL",
    "amqp://trinetra_admin:trinetra_rabbit_pass@localhost:5672/"
)

# ─── Queue Definitions ────────────────────────────────────────────────────────
QUEUES = {
    "evidence.uploaded":          "evidence.uploaded",
    "evidence.processed":         "evidence.processed",
    "fraud.analysis.complete":    "fraud.analysis.complete",
    "verdict.generated":          "verdict.generated",
    "integration.events":         "integration.events",
    "integration.events.dlq":     "integration.events.dlq",   # Dead Letter Queue
}

DEAD_LETTER_QUEUE = "integration.events.dlq"


class MessageBus:
    """
    Thin async wrapper around aio-pika for RabbitMQ messaging.

    Usage (publisher):
        bus = MessageBus()
        await bus.connect()
        await bus.publish("evidence.uploaded", {"evidence_id": "...", "claim_id": "..."})
        await bus.close()

    Usage (consumer):
        bus = MessageBus()
        await bus.connect()
        await bus.subscribe("evidence.uploaded", my_handler)
        await asyncio.Future()  # run forever
    """

    def __init__(self) -> None:
        self._connection: Optional[aio_pika.RobustConnection] = None
        self._channel: Optional[aio_pika.Channel] = None

    async def connect(self) -> None:
        """Establish connection and declare all queues."""
        self._connection = await connect_robust(RABBITMQ_URL)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=10)

        # Declare main queues + DLQ
        for queue_name in QUEUES.values():
            await self._channel.declare_queue(
                queue_name,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": "",
                    "x-dead-letter-routing-key": DEAD_LETTER_QUEUE,
                } if queue_name != DEAD_LETTER_QUEUE else None,
            )

        logger.info("MessageBus connected to RabbitMQ and queues declared.")

    async def publish(self, queue_name: str, payload: Dict[str, Any]) -> None:
        """Publish a JSON-serialized message to a named queue."""
        if self._channel is None:
            raise RuntimeError("MessageBus not connected. Call await bus.connect() first.")

        body = json.dumps(payload, default=str).encode()
        message = Message(
            body=body,
            content_type="application/json",
            delivery_mode=DeliveryMode.PERSISTENT,
        )

        queue = QUEUES.get(queue_name, queue_name)
        await self._channel.default_exchange.publish(message, routing_key=queue)
        logger.debug("Published to %s: %s", queue_name, payload)

    async def subscribe(
        self,
        queue_name: str,
        handler: Callable[[Dict[str, Any]], None],
        auto_ack: bool = False,
    ) -> None:
        """Subscribe to a queue and call handler for each message."""
        if self._channel is None:
            raise RuntimeError("MessageBus not connected. Call await bus.connect() first.")

        queue = await self._channel.declare_queue(queue_name, durable=True)

        async def _process_message(message: AbstractIncomingMessage) -> None:
            try:
                payload = json.loads(message.body.decode())
                await handler(payload)
                await message.ack()
            except Exception as exc:
                logger.error("Error handling message from %s: %s", queue_name, exc)
                await message.nack(requeue=False)  # Send to DLQ

        await queue.consume(_process_message)
        logger.info("Subscribed to queue: %s", queue_name)

    async def close(self) -> None:
        if self._connection:
            await self._connection.close()
            logger.info("MessageBus connection closed.")


# ─── Singleton Instance ───────────────────────────────────────────────────────
_bus: Optional[MessageBus] = None


async def get_message_bus() -> MessageBus:
    global _bus
    if _bus is None:
        _bus = MessageBus()
        await _bus.connect()
    return _bus


async def publish_event(queue_name: str, payload: Dict[str, Any]) -> None:
    """Convenience function: get shared bus and publish a single event."""
    bus = await get_message_bus()
    await bus.publish(queue_name, payload)
