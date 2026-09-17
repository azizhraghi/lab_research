"""Machine-to-machine field gateway ingestion endpoint.

This router intentionally has no Supabase user dependency. A device proves its
identity with its own provisioned key in ``X-Sensor-Token``; the main API
registers it separately from protected researcher routes.
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import select

from agents.digitaltwin.agent import digital_twin_agent
from agents.digitaltwin.models import SensorDevice
from agents.digitaltwin.schemas import GatewayReadingPayload, SensorReadingResponse
from shared.database import AsyncSessionLocal
from shared.gateway_security import gateway_token_matches
from shared.outbox import enqueue_event, outbox_dispatcher
from shared.schemas import Event


router = APIRouter(tags=["field-gateway"])


@router.post("/readings", response_model=SensorReadingResponse)
async def ingest_gateway_reading(
    data: GatewayReadingPayload,
    x_sensor_code: str = Header(..., alias="X-Sensor-Code"),
    x_sensor_token: str = Header(..., alias="X-Sensor-Token"),
):
    """Accept one reading from an active registered gateway.

    Neither the code nor token is accepted in a URL/query string, avoiding
    accidental inclusion in proxy logs. The token is compared only as an HMAC
    hash and its plaintext is never written to the database.
    """
    async with AsyncSessionLocal() as db:
        device = (await db.execute(
            select(SensorDevice).where(SensorDevice.code == x_sensor_code)
        )).scalar_one_or_none()
        if device is None or not gateway_token_matches(x_sensor_token, device.token_hash):
            raise HTTPException(status_code=401, detail="Invalid gateway credentials")
        if not device.active:
            raise HTTPException(status_code=403, detail="Sensor device is disabled")

        now = datetime.utcnow()
        try:
            reading = await digital_twin_agent.ingest_reading(
                db,
                device.parcel_id,
                {
                    **data.model_dump(exclude={"battery_percent"}),
                    "sensor_code": device.code,
                    "quality_flag": "pending",
                    "review_status": "pending_validation",
                    "data_origin": "gateway",
                },
            )
            device.battery_percent = data.battery_percent
            device.last_contact_at = now
            device.last_upload_at = now
            device.consecutive_upload_failures = 0
            device.last_error = None
            await enqueue_event(db, "events", Event(
                id=f"gateway-reading-{device.id}-{reading.id}",
                type="twin.reading_recorded",
                source_agent="field_gateway",
                payload={
                    "parcel_id": device.parcel_id,
                    "reading_id": reading.id,
                    "reading": SensorReadingResponse.model_validate(reading).model_dump(mode="json"),
                },
            ))
            await db.commit()
            await db.refresh(reading)
        except Exception as exc:
            await db.rollback()
            # Best-effort health accounting; do not mask the original failure.
            device = await db.get(SensorDevice, device.id)
            if device is not None:
                device.consecutive_upload_failures += 1
                device.last_error = f"{type(exc).__name__}: {exc}"[:500]
                device.last_contact_at = now
                await db.commit()
            raise

    outbox_dispatcher.notify()
    return reading
