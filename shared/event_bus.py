# -*- coding: utf-8 -*-
"""Event Bus – Configurable event bus with Redis Streams (default), Kafka, and InMemory.

Original: Redis Streams (your monorepo).
Added: KafkaEventBus, InMemoryEventBus, and factory from Friend 2.
"""
import json
import asyncio
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Callable, Any, Awaitable, Optional

import redis.asyncio as redis

from shared.config import settings
from shared.schemas import Event

EventHandler = Callable[[Event], Awaitable[None]]


# ── Abstract Base ─────────────────────────────────────────────────────

class EventBusBase(ABC):
    """Contract all event bus implementations must respect."""

    @abstractmethod
    async def publish(self, stream: str, event: Event) -> str:
        raise NotImplementedError

    @abstractmethod
    async def subscribe(self, stream: str, handler: EventHandler) -> None:
        raise NotImplementedError


# ── Redis Streams (your original, default) ────────────────────────────

class RedisStreamsEventBus(EventBusBase):
    """Your original Redis Streams implementation."""

    def __init__(self):
        self._redis_client: Optional[redis.Redis] = None

    @property
    def redis_client(self):
        """Lazy Redis connection — only connects when actually used."""
        if self._redis_client is None:
            self._redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        return self._redis_client

    async def publish(self, stream_name: str, event: Event) -> str:
        """Publish to the stream, raising on failure.

        A dropped event means subscribed agents silently miss work they were
        supposed to react to, so an unreachable Redis is an error the caller
        (and the operator) must see — never a printed line and a fake "".
        """
        event_dict = event.model_dump(mode='json')
        payload = {"data": json.dumps(event_dict)}
        return await self.redis_client.xadd(stream_name, payload)

    async def subscribe(self, stream_name: str, group_name: str = None,
                        consumer_name: str = None,
                        callback: EventHandler = None,
                        handler: EventHandler = None) -> None:
        """Subscribe to a Redis stream.

        Supports both the original signature (group_name, consumer_name, callback)
        and the simplified signature (handler) for compatibility.
        """
        actual_handler = callback or handler
        if actual_handler is None:
            return

        _group = group_name or f"{stream_name}-group"
        _consumer = consumer_name or f"{stream_name}-consumer"

        try:
            await self.redis_client.xgroup_create(stream_name, _group, id="$", mkstream=True)
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

        while True:
            try:
                messages = await self.redis_client.xreadgroup(
                    groupname=_group,
                    consumername=_consumer,
                    streams={stream_name: ">"},
                    count=1,
                    block=5000,
                )

                for stream, msgs in messages:
                    for message_id, message_data in msgs:
                        raw_data = message_data.get("data")
                        if raw_data:
                            event_data = json.loads(raw_data)
                            event = Event(**event_data)
                            await actual_handler(event)
                            await self.redis_client.xack(stream_name, _group, message_id)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                # Consumer loop: log and keep polling rather than dying — but
                # say it loudly; a silent consumer is a lost agent.
                print(f"[EventBus] Redis consumer error on {stream_name}: {e}")


# ── InMemory (from Friend 2, useful for testing) ──────────────────────

class InMemoryEventBus(EventBusBase):
    """In-memory event bus — no external dependencies, ideal for tests and dev.

    Publish does NOT await handlers inline. A single background worker drains a
    FIFO queue, so a slow subscriber (bibliometrie's Scholar fetch, PDF work)
    runs outside the coroutine that published the event — before, a scrape
    request stayed open for the entire downstream chain it triggered.

    One worker, not one task per handler, is deliberate: handlers still run in
    subscription order (qualite persists a validation before the twin reacts to
    it), which the guarded startup sequence in api/main.py depends on for an
    honest audit trail. The tradeoff is head-of-line blocking between events —
    irrelevant at dev scale, and production uses Redis Streams anyway.

    Handler exceptions are logged and never kill the worker; a worker that dies
    anyway is restarted by the next publish.
    """

    # Last-N published events kept for debugging; unbounded growth would leak
    # on long-running dev servers. Nothing reads this yet.
    HISTORY_LIMIT = 500

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self.history: list[tuple[str, Event]] = []
        self._queue: Optional[asyncio.Queue] = None
        self._worker: Optional[asyncio.Task] = None

    def _ensure_worker(self) -> None:
        if self._worker is None or self._worker.done():
            self._queue = asyncio.Queue()
            self._worker = asyncio.create_task(self._drain())
            self._worker.add_done_callback(self._on_worker_exit)

    @staticmethod
    def _on_worker_exit(task: asyncio.Task) -> None:
        if task.cancelled():
            return
        exc = task.exception()
        if exc is not None:
            # Should be unreachable — handlers are individually guarded — but a
            # dead dispatcher must at least be visible in the logs.
            print(f"[EventBus] Dispatch worker died unexpectedly: {type(exc).__name__}: {exc}")

    async def _drain(self) -> None:
        while True:
            stream, event = await self._queue.get()
            try:
                for handler in self._subscribers.get(stream, []):
                    try:
                        await handler(event)
                    except Exception as e:
                        print(
                            f"[EventBus] Handler for '{event.type}' raised: "
                            f"{type(e).__name__}: {e}"
                        )
            finally:
                self._queue.task_done()

    async def publish(self, stream: str, event: Event) -> str:
        self.history.append((stream, event))
        if len(self.history) > self.HISTORY_LIMIT:
            del self.history[:-self.HISTORY_LIMIT]
        self._ensure_worker()
        self._queue.put_nowait((stream, event))
        return event.id

    async def subscribe(self, stream: str, handler: EventHandler, **kwargs) -> None:
        self._subscribers[stream].append(handler)


# ── Kafka (from Friend 2) ────────────────────────────────────────────

class KafkaEventBus(EventBusBase):
    """Kafka-backed event bus using aiokafka."""

    def __init__(self, bootstrap_servers: str = "localhost:9092") -> None:
        self._bootstrap_servers = bootstrap_servers
        self._producer = None
        self._tasks: list[asyncio.Task] = []

    async def _get_producer(self):
        if self._producer is None:
            from aiokafka import AIOKafkaProducer
            self._producer = AIOKafkaProducer(bootstrap_servers=self._bootstrap_servers)
            await self._producer.start()
        return self._producer

    async def publish(self, stream: str, event: Event) -> str:
        producer = await self._get_producer()
        message = event.model_dump_json().encode("utf-8")
        await producer.send_and_wait(stream, message)
        return event.id

    async def _consume(self, stream: str, handler: EventHandler) -> None:
        from aiokafka import AIOKafkaConsumer
        consumer = AIOKafkaConsumer(
            stream,
            bootstrap_servers=self._bootstrap_servers,
            auto_offset_reset="latest",
            group_id=f"{stream}-group",
        )
        await consumer.start()
        try:
            async for message in consumer:
                event = Event.model_validate_json(message.value.decode("utf-8"))
                await handler(event)
        finally:
            await consumer.stop()

    async def subscribe(self, stream: str, handler: EventHandler, **kwargs) -> None:
        task = asyncio.create_task(self._consume(stream, handler))
        self._tasks.append(task)


# ── Factory (from Friend 2's state.py) ────────────────────────────────

def create_event_bus() -> EventBusBase:
    """Create the correct event bus based on EVENT_BUS_TYPE config."""
    bus_type = settings.EVENT_BUS_TYPE.lower()
    if bus_type == "kafka":
        print("[EventBus] Using Kafka")
        return KafkaEventBus(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
    if bus_type == "memory":
        print("[EventBus] Using InMemory")
        return InMemoryEventBus()
    # Default: Redis Streams
    print("[EventBus] Using Redis Streams")
    return RedisStreamsEventBus()


# Module-level singleton — used by shared.base_agent and all agents
event_bus = create_event_bus()
