from __future__ import annotations 
from abc import ABC, abstractmethod 
from collections import defaultdict 
from typing import Awaitable, Callable
from app.schemas.events import Event 
import asyncio
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import redis.asyncio as redis 

EventHandler = Callable[[Event], Awaitable[None]]

class EventBus(ABC):
    """contract commun doit etre respecter par toute implementation du bus"""

    @abstractmethod
    async def publish(self, stream: str, event: Event) -> str:
        """publie un evenement sur um stream donnee , retourne son id"""
        raise NotImplementedError
    
    @abstractmethod
    async def subscribe(self, stream: str, handler: EventHandler) -> None:
        """enregistre un handler appele pour chaque futur evenement du stream"""
        raise NotImplementedError 
    

class InMemoryEventBus(EventBus):
    def __init__(self)->None:
        self._subscribers: dict[str, list[EventHandler]]=defaultdict(list)
        self.history :list[tuple[str, Event]]=[]  #pratique pour les tests

    async def publish(self , stream: str, event: Event)-> str:
        self.history.append((stream, event))
        for handler in self._subscribers.get(stream,[]):
            await handler(event)
        return event.id
    
    async def subscribe(self,stream:str,handler:EventHandler)->None:
        self._subscribers[stream].append(handler)


class KafkaEventBus(EventBus):
    def __init__(self, bootstrap_servers: str = "localhost:9092") -> None:
        self._bootstrap_servers = bootstrap_servers
        self._producer: AIOKafkaProducer | None = None
        self._tasks: list[asyncio.Task] = []
    
    async def _get_producer(self) -> AIOKafkaProducer:
        if self._producer is None:
            self._producer = AIOKafkaProducer(bootstrap_servers=self._bootstrap_servers)
            await self._producer.start()
        return self._producer

    async def publish(self, stream: str, event: Event) -> str:
        producer = await self._get_producer()
        message = event.model_dump_json().encode("utf-8")
        await producer.send_and_wait(stream, message)
        return event.id
    
    async def _consommer(self, stream: str, handler: EventHandler) -> None:
        consumer = AIOKafkaConsumer(
            stream,
            bootstrap_servers=self._bootstrap_servers,
            auto_offset_reset="latest",
            group_id=f"{stream}-group"
        )
        await consumer.start()
        try:
            async for message in consumer:
                event = Event.model_validate_json(message.value.decode("utf-8"))
                await handler(event)
        finally:
            await consumer.stop()

    async def subscribe(self, stream: str, handler: EventHandler) -> None:
        task = asyncio.create_task(self._consommer(stream, handler))
        self._tasks.append(task)


class RedisEventBus(EventBus):
    def __init__(self, host: str = "localhost", port: int = 6379) -> None:
        self._client = redis.Redis(host=host, port=port)
        self._tasks: list[asyncio.Task] = []
    
    async def publish(self, stream: str, event: Event) -> str:
        message = event.model_dump_json()
        await self._client.publish(stream, message)
        return event.id
    
    async def _consommer(self, stream: str, handler: EventHandler) -> None:
        pubsub = self._client.pubsub()
        await pubsub.subscribe(stream)
        try:
            while True:
                message = await pubsub.get_message(timeout=1.0)
                if message and message["type"] == "message":
                    event = Event.model_validate_json(message["data"])
                    await handler(event)
        finally:
            await pubsub.unsubscribe(stream)

    async def subscribe(self, stream: str, handler: EventHandler) -> None:
        task = asyncio.create_task(self._consommer(stream, handler))
        self._tasks.append(task)
