"""Durable at-least-once event delivery for agent workflows.

Business code stores an event in `system_outbox` in the same transaction as its
domain change. The dispatcher publishes it later and only marks it delivered
after the transport acknowledges it. A duplicate may occur after a process
crash between publish and acknowledgement, so consumers must remain idempotent.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import Column, DateTime, Integer, JSON, String, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from shared.config import settings
from shared.database import AsyncSessionLocal, Base
from shared.event_bus import event_bus
from shared.schemas import Event


logger = logging.getLogger("lrste.outbox")


class OutboxEvent(Base):
    __tablename__ = "system_outbox"

    id = Column(String, primary_key=True)
    stream = Column(String, nullable=False, index=True)
    event = Column(JSON, nullable=False)
    status = Column(String, nullable=False, default="pending", index=True)
    attempts = Column(Integer, nullable=False, default=0)
    next_attempt_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    locked_until = Column(DateTime, nullable=True, index=True)
    last_error = Column(String, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


async def enqueue_event(db: AsyncSession, stream: str, event: Event) -> OutboxEvent:
    """Add an event to an existing business transaction, without publishing it."""
    existing = await db.get(OutboxEvent, event.id)
    if existing is not None:
        return existing
    row = OutboxEvent(
        id=event.id,
        stream=stream,
        event=event.model_dump(mode="json"),
    )
    db.add(row)
    return row


class OutboxDispatcher:
    """Single-process dispatcher; claim leases keep retry work recoverable."""

    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._wake = asyncio.Event()
        self._stopping = False

    async def start(self) -> None:
        self._stopping = False
        await self._recover_expired_claims()
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run(), name="lrste-outbox-dispatcher")
        self.notify()

    async def stop(self) -> None:
        self._stopping = True
        self._wake.set()
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    def notify(self) -> None:
        self._wake.set()

    async def _run(self) -> None:
        while not self._stopping:
            try:
                await self.dispatch_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                # The outbox itself must not disappear because the database or
                # broker is briefly unavailable. The next polling cycle will
                # retry; readiness makes the problem visible to operators.
                logger.exception("outbox_dispatch_cycle_failed")
            self._wake.clear()
            try:
                await asyncio.wait_for(self._wake.wait(), timeout=settings.OUTBOX_POLL_SECONDS)
            except asyncio.TimeoutError:
                pass

    async def _recover_expired_claims(self) -> None:
        now = datetime.utcnow()
        async with AsyncSessionLocal() as db:
            await db.execute(
                update(OutboxEvent)
                .where(OutboxEvent.status == "dispatching", OutboxEvent.locked_until < now)
                .values(status="pending", locked_until=None)
            )
            await db.commit()

    async def dispatch_once(self) -> None:
        # A restart can happen before the previous worker's lease expires.
        # Recover on every cycle so those claims do not need another restart.
        await self._recover_expired_claims()
        now = datetime.utcnow()
        async with AsyncSessionLocal() as db:
            rows = (await db.execute(
                select(OutboxEvent.id)
                .where(OutboxEvent.status == "pending", OutboxEvent.next_attempt_at <= now)
                .order_by(OutboxEvent.created_at)
                .limit(settings.OUTBOX_BATCH_SIZE)
            )).scalars().all()

        for event_id in rows:
            await self._dispatch_one(event_id)

    async def _dispatch_one(self, event_id: str) -> None:
        now = datetime.utcnow()
        lease_until = now + timedelta(seconds=settings.OUTBOX_CLAIM_SECONDS)
        async with AsyncSessionLocal() as db:
            claimed = await db.execute(
                update(OutboxEvent)
                .where(OutboxEvent.id == event_id, OutboxEvent.status == "pending")
                .values(status="dispatching", locked_until=lease_until)
            )
            await db.commit()
            if claimed.rowcount != 1:
                return
            row = await db.get(OutboxEvent, event_id)
            if row is None:
                return
            stream = row.stream
            payload = row.event

        try:
            await event_bus.publish(stream, Event.model_validate(payload))
        except Exception as exc:
            await self._record_failure(event_id, exc)
            return

        async with AsyncSessionLocal() as db:
            row = await db.get(OutboxEvent, event_id)
            if row is not None:
                row.status = "delivered"
                row.delivered_at = datetime.utcnow()
                row.locked_until = None
                row.last_error = None
                await db.commit()
        logger.info("outbox_delivered", extra={"event_id": event_id, "stream": stream})

    async def _record_failure(self, event_id: str, exc: Exception) -> None:
        async with AsyncSessionLocal() as db:
            row = await db.get(OutboxEvent, event_id)
            if row is None:
                return
            row.attempts += 1
            row.locked_until = None
            row.last_error = f"{type(exc).__name__}: {exc}"[:2000]
            if row.attempts >= settings.OUTBOX_MAX_ATTEMPTS:
                row.status = "failed"
            else:
                # Bounded exponential backoff: 2, 4, 8 … seconds by default.
                seconds = min(settings.OUTBOX_RETRY_SECONDS * (2 ** (row.attempts - 1)), 300)
                row.status = "pending"
                row.next_attempt_at = datetime.utcnow() + timedelta(seconds=seconds)
            await db.commit()
            logger.error(
                "outbox_delivery_failed",
                extra={"event_id": event_id, "attempts": row.attempts, "status": row.status},
                exc_info=exc,
            )

    async def stats(self) -> dict[str, int]:
        async with AsyncSessionLocal() as db:
            rows = (await db.execute(
                select(OutboxEvent.status, func.count(OutboxEvent.id)).group_by(OutboxEvent.status)
            )).all()
        counts = {status: count for status, count in rows}
        return {
            "pending": counts.get("pending", 0),
            "dispatching": counts.get("dispatching", 0),
            "delivered": counts.get("delivered", 0),
            "failed": counts.get("failed", 0),
        }

    async def list_failed(self, limit: int = 50) -> list[OutboxEvent]:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OutboxEvent)
                .where(OutboxEvent.status == "failed")
                .order_by(OutboxEvent.created_at.desc())
                .limit(limit)
            )
            return result.scalars().all()

    async def retry(self, event_id: str) -> bool:
        async with AsyncSessionLocal() as db:
            row = await db.get(OutboxEvent, event_id)
            if row is None or row.status != "failed":
                return False
            row.status = "pending"
            row.attempts = 0
            row.next_attempt_at = datetime.utcnow()
            row.locked_until = None
            row.last_error = None
            await db.commit()
        self.notify()
        return True


outbox_dispatcher = OutboxDispatcher()
