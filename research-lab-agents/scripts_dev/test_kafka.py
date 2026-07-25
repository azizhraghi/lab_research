import asyncio
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer


async def main():
    # 1. Instanciation du producer avec l'adresse du serveur Kafka
    producer = AIOKafkaProducer(bootstrap_servers="localhost:9092")

    # 2. Démarrage du producer
    await producer.start()

    try:
        # 3. Envoi du message en bytes sur le topic "test-topic"
        await producer.send_and_wait("test-topic", b"Hello Kafka depuis Python")
        print(" Message envoyé avec succès à Kafka sur 'test-topic' !")
    finally:
        # 4. Arrêt propre du producer
        await producer.stop()


async def lire_messages():
    consumer = AIOKafkaConsumer(
        "test-topic",
        bootstrap_servers="localhost:9092",
        auto_offset_reset="earliest",
        group_id="test-group"
    )
    await consumer.start()
    try:
        async for message in consumer:
            print(f" Message reçu : {message.value.decode()}")
            break
    finally:
        await consumer.stop()

# Lancement du script asynchrone
if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(lire_messages())
