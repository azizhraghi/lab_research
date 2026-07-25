import asyncio
from app.core.event_bus import RedisEventBus
from app.schemas.events import Event


async def handler_test(event: Event) -> None:
    print(f" Handler appelé avec l'événement : {event.type} — payload: {event.payload}")


async def main():
    bus = RedisEventBus()

    await bus.subscribe("test.redis_eventbus", handler_test)

    print(" Attente de l'initialisation du consumer...")
    await asyncio.sleep(2)

    print(" Envoi du message...")
    await bus.publish("test.redis_eventbus", Event(
        type="test.redis_eventbus",
        source_agent="test_manuel",
        payload={"message": "ça marche via RedisEventBus !"}
    ))

    print(" Attente de la réception...")
    await asyncio.sleep(3)

    print(" Fin du test.")


if __name__ == "__main__":
    asyncio.run(main())