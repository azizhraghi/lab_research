"""Durable consumer receipts for at-least-once agent event delivery.

Each receiving agent claims an event before handling it and records completion
after the handler returns. This prevents a broker retry from creating duplicate
alerts, recommendations, or planning work. A short lease makes an interrupted
claim recoverable after a process crash.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import Column, DateTime, Integer, String, func, select
from sqlalchemy.exc import IntegrityError

from shared.database import AsyncSessionLocal, Base


class EventReceipt(Base):
    __tablename__ = "system_event_receipts"

    agent_name = Column(String, primary_key=True)
    event_id = Column(String, primary_key=True)
    status = Column(String, nullable=False, default="processing", index=True)
    attempts = Column(Integer, nullable=False, default=1)
    locked_until = Column(DateTime, nullable=True, index=True)
    last_error = Column(String, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


_LEASE_SECONDS = 120


async def claim_event(agent_name: str, event_id: str) -> bool:
    """Claim one delivery unless this agent has already completed it."""
    now = datetime.utcnow()
    async with AsyncSessionLocal() as db:
        receipt = await db.get(EventReceipt, (agent_name, event_id))
        if receipt is not None:
            if receipt.status == "processed":
                return False
            if receipt.locked_until and receipt.locked_until > now:
                return False
            receipt.status = "processing"
            receipt.attempts += 1
            receipt.locked_until = now + timedelta(seconds=_LEASE_SECONDS)
            receipt.last_error = None
            await db.commit()
            return True

        db.add(EventReceipt(
            agent_name=agent_name,
            event_id=event_id,
            locked_until=now + timedelta(seconds=_LEASE_SECONDS),
        ))
        try:
            await db.commit()
            return True
        except IntegrityError:
            # Another worker won the primary-key race and is processing it.
            await db.rollback()
            return False


async def mark_event_processed(agent_name: str, event_id: str) -> None:
    async with AsyncSessionLocal() as db:
        receipt = await db.get(EventReceipt, (agent_name, event_id))
        if receipt is None:
            return
        receipt.status = "processed"
        receipt.locked_until = None
        receipt.last_error = None
        receipt.processed_at = datetime.utcnow()
        await db.commit()


async def release_event_claim(agent_name: str, event_id: str, error: Exception) -> None:
    """Make a failed delivery eligible for the broker's next retry."""
    async with AsyncSessionLocal() as db:
        receipt = await db.get(EventReceipt, (agent_name, event_id))
        if receipt is None or receipt.status == "processed":
            return
        receipt.status = "pending"
        receipt.locked_until = None
        receipt.last_error = f"{type(error).__name__}: {error}"[:2000]
        await db.commit()


async def receipt_stats() -> dict[str, int]:
    """Small operational summary of consumer delivery state."""
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(
            select(EventReceipt.status, func.count()).group_by(EventReceipt.status)
        )).all()
    counts = {status: count for status, count in rows}
    return {
        "processed": counts.get("processed", 0),
        "processing": counts.get("processing", 0),
        "pending": counts.get("pending", 0),
    }
