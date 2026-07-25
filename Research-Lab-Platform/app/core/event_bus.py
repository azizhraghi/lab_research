from __future__ import annotations 
from abc import ABC, abstractmethod 
from collections import defaultdict 
from typing import Awaitable, Callable
from app.schemas.events import Event 

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
    

