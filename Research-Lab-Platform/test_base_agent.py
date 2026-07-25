import asyncio

from app.core.base_agent import BaseAgent
from app.core.event_bus import InMemoryEventBus
from app.schemas.events import Event


class DummyAgent(BaseAgent):
    """Un agent factice, juste pour tester que BaseAgent fonctionne."""

    async def on_start(self) -> None:
        print(f"[{self.name}] demarrage...")

    async def on_stop(self) -> None:
        print(f"[{self.name}] arret...")

    async def handle_event(self, event: Event) -> None:
        print(f"[{self.name}] a recu l'evenement '{event.type}'")


async def main():
    bus = InMemoryEventBus()
    agent = DummyAgent(name="dummy", event_bus=bus)

    print(f"Statut initial : {agent.status}")
    assert agent.status == "stopped"

    await agent.start()
    print(f"Statut apres start() : {agent.status}")
    assert agent.status == "running"

    await bus.subscribe("test.event", agent.handle_event)
    await bus.publish("test.event", Event(type="test.event", source_agent="test"))

    await agent.stop()
    print(f"Statut apres stop() : {agent.status}")
    assert agent.status == "stopped"

    print("OK : BaseAgent fonctionne comme prevu.")


asyncio.run(main())