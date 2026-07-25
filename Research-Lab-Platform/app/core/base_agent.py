from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Literal
from app.core.event_bus import EventBus
from app.schemas.events import Event

AgentStatus = Literal["stopped","running","degraded"]


class BaseAgent(ABC):
    """classe de base pour tous les agents du systeme"""

    def __init__(self, name:str, event_bus:EventBus) ->None:
        self.name =name
        self.event_bus= event_bus
        self.status: AgentStatus ="stopped"

    async def start(self)->None:
        await self.on_start()
        self.status="running"
    async def stop(self)->None:
        await self.on_stop()
        self.status="stopped"
    
    @abstractmethod
    async def on_start(self)->None:
        raise NotImplementedError
    @abstractmethod
    async def on_stop(self)->None:
        raise NotImplementedError
    @abstractmethod
    async def handle_event(self,event:Event)->None:
        raise NotImplementedError
