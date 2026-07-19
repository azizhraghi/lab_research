import json
import redis.asyncio as redis
from typing import Callable, Any, Awaitable, Optional
from shared.config import settings
from shared.schemas import Event

class EventBus:
    def __init__(self):
        self._redis_client: Optional[redis.Redis] = None
    
    @property
    def redis_client(self):
        """Lazy Redis connection — only connects when actually used."""
        if self._redis_client is None:
            self._redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        return self._redis_client
    
    async def publish(self, stream_name: str, event: Event) -> str:
        """Publish an event to a Redis stream."""
        try:
            event_dict = event.model_dump(mode='json')
            payload = {"data": json.dumps(event_dict)}
            message_id = await self.redis_client.xadd(stream_name, payload)
            return message_id
        except Exception as e:
            print(f"[EventBus] Redis not available, skipping publish: {e}")
            return ""

    async def subscribe(self, stream_name: str, group_name: str, consumer_name: str, callback: Callable[[Event], Awaitable[None]]):
        """Subscribe to a Redis stream using a consumer group."""
        try:
            await self.redis_client.xgroup_create(stream_name, group_name, id="$", mkstream=True)
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
        except Exception as e:
            print(f"[EventBus] Redis not available for subscribe: {e}")
            return
        
        while True:
            try:
                messages = await self.redis_client.xreadgroup(
                    groupname=group_name,
                    consumername=consumer_name,
                    streams={stream_name: ">"},
                    count=1,
                    block=5000
                )
                
                for stream, msgs in messages:
                    for message_id, message_data in msgs:
                        raw_data = message_data.get("data")
                        if raw_data:
                            event_data = json.loads(raw_data)
                            event = Event(**event_data)
                            await callback(event)
                            await self.redis_client.xack(stream_name, group_name, message_id)
            except Exception as e:
                print(f"Error processing stream {stream_name}: {e}")

event_bus = EventBus()
