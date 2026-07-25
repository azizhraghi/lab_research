import asyncio
import redis.asyncio as redis 


async def main():
    client = redis.Redis(host="localhost",port=6379)
    pubsub = client.pubsub()
    await pubsub.subscribe("test-channel")
    await client.publish("test-channel","hello Redis depuis python")
    while True:
        message = await pubsub.get_message(timeout=5)
        if message and message["type"] == "message":
            print(f" Message reçu : {message['data'].decode()}")
            break

asyncio.run(main())