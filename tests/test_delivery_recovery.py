"""Delivery fault injection against an isolated database; no live broker."""
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, patch
from uuid import uuid4


class DeliveryRecoveryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from shared import outbox
        self.outbox = outbox
        self.directory = tempfile.TemporaryDirectory(prefix="lrste-delivery-")
        self.engine = create_async_engine(
            "sqlite+aiosqlite:///" + (Path(self.directory.name) / "delivery.db").as_posix())
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as connection:
            await connection.run_sync(outbox.OutboxEvent.__table__.create)
        self.session_patch = patch.object(outbox, "AsyncSessionLocal", self.sessions)
        self.session_patch.start()
        self.publisher = AsyncMock()
        self.bus_patch = patch.object(outbox, "event_bus", self.publisher)
        self.bus_patch.start()
        self.dispatcher = outbox.OutboxDispatcher()

    async def asyncTearDown(self):
        self.bus_patch.stop()
        self.session_patch.stop()
        await self.engine.dispose()
        self.directory.cleanup()

    async def event(self, **fields):
        from shared.schemas import Event
        event = Event(id=str(uuid4()), type="recovery.fixture", source_agent="test", payload={})
        async with self.sessions() as db:
            row = await self.outbox.enqueue_event(db, "recovery.fixture", event)
            for key, value in fields.items():
                setattr(row, key, value)
            await db.commit()
        return event.id

    async def row(self, event_id):
        async with self.sessions() as db:
            return await db.get(self.outbox.OutboxEvent, event_id)

    async def test_claim_expiring_after_restart_is_recovered_during_polling(self):
        event_id = await self.event(status="dispatching",
            locked_until=datetime.utcnow() + timedelta(minutes=1))
        await self.dispatcher._recover_expired_claims()
        await self.dispatcher.dispatch_once()
        self.publisher.publish.assert_not_awaited()
        async with self.sessions() as db:
            row = await db.get(self.outbox.OutboxEvent, event_id)
            row.locked_until = datetime.utcnow() - timedelta(seconds=1)
            await db.commit()
        await self.dispatcher.dispatch_once()
        self.assertEqual((await self.row(event_id)).status, "delivered")
        self.publisher.publish.assert_awaited_once()
        await self.dispatcher.dispatch_once()
        self.publisher.publish.assert_awaited_once()

    async def test_broker_failure_survives_dispatcher_replacement(self):
        event_id = await self.event()
        self.publisher.publish.side_effect = ConnectionError("injected outage")
        with patch.object(self.outbox.settings, "OUTBOX_RETRY_SECONDS", 0):
            await self.dispatcher.dispatch_once()
        row = await self.row(event_id)
        self.assertEqual(row.status, "pending")
        self.assertEqual(row.attempts, 1)
        self.assertIn("injected outage", row.last_error)
        self.publisher.publish.side_effect = None
        await self.outbox.OutboxDispatcher().dispatch_once()
        row = await self.row(event_id)
        self.assertEqual(row.status, "delivered")
        self.assertIsNotNone(row.delivered_at)
        self.assertIsNone(row.last_error)

    async def test_exhausted_delivery_requires_explicit_retry(self):
        event_id = await self.event()
        self.publisher.publish.side_effect = ConnectionError("injected outage")
        with patch.object(self.outbox.settings, "OUTBOX_MAX_ATTEMPTS", 1):
            await self.dispatcher.dispatch_once()
        self.assertEqual((await self.row(event_id)).status, "failed")
        self.assertEqual((await self.dispatcher.stats())["failed"], 1)
        await self.dispatcher.dispatch_once()
        self.publisher.publish.assert_awaited_once()
        self.assertFalse(await self.dispatcher.retry(str(uuid4())))
        self.assertTrue(await self.dispatcher.retry(event_id))
        self.publisher.publish.side_effect = None
        await self.dispatcher.dispatch_once()
        self.assertEqual((await self.row(event_id)).status, "delivered")
        self.assertFalse(await self.dispatcher.retry(event_id))
