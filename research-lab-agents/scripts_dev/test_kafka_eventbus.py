import asyncio
from app.core.event_bus import KafkaEventBus
from app.schemas.events import Event


async def handler_test(event: Event) -> None:
    print(f" Handler appelé avec l'événement : {event.type} — payload: {event.payload}")


async def main():
    bus = KafkaEventBus()

    await bus.subscribe("test.kafka_eventbus", handler_test)

    print(" Attente de l'initialisation du consumer...")
    await asyncio.sleep(8)

    print(" Envoi du message...")
    await bus.publish("test.kafka_eventbus", Event(
        type="test.kafka_eventbus",
        source_agent="test_manuel",
        payload={"message": "ça marche via KafkaEventBus !"}
    ))

    print(" Attente de la réception...")
    await asyncio.sleep(5)

    print(" Fin du test.")

if __name__ == "__main__":
    asyncio.run(main())