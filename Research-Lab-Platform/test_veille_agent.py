import asyncio
from app.core.event_bus import InMemoryEventBus       # local event bus for testing
from app.agents.veille_agent import VeilleAgent        # your agent
from app.schemas.events import Event                   # event schema

async def main():
    bus = InMemoryEventBus()                           # creates a local in-memory bus

    # tracks events published by the agent
    received_events = []

    async def on_article_discovered(event: Event):
        received_events.append(event)
        print(f"  EVENT RECEIVED: {event.payload.get('title', '')[:60]}")

    # subscribes to article.discovered events before starting the agent
    await bus.subscribe("article.discovered", on_article_discovered)

    # creates and starts your agent
    agent = VeilleAgent(name="veille", event_bus=bus)
    print(f"Status before start: {agent.status}")

    await agent.start()

    print(f"\nStatus after start: {agent.status}")
    print(f"Total events published: {len(received_events)}")

    await agent.stop()
    print(f"Status after stop: {agent.status}")

asyncio.run(main())