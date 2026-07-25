import asyncio
from app.core.event_bus import InMemoryEventBus
from app.schemas.events import Event


async def main():
    bus = InMemoryEventBus()
    received = []

    async def on_project_updated(event: Event):
        received.append(event)
        print(f"  -> handler a recu : {event.type} (payload={event.payload})")

    await bus.subscribe("project.updated", on_project_updated)

    print("Publication d'un evenement...")
    event = Event(
        type="project.updated",
        source_agent="mis",
        payload={"project_id": "PRJ-042", "field": "budget"},
    )
    event_id = await bus.publish("project.updated", event)
    print(f"Event publie avec id={event_id}")
    print(f"Nombre d'evenements recus par le handler : {len(received)}")
    assert len(received) == 1
    print("OK : tout fonctionne comme prevu.")


asyncio.run(main())