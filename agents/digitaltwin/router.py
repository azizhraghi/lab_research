import csv
import io
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.security import User, require_roles
from shared.schemas import Event
from agents.digitaltwin.models import (
    CalibrationProfile,
    IrrigationEvent,
    IrrigationRecommendation,
    Parcel,
    SensorReading,
    SimulationScenario,
    WeatherForecast,
)
from agents.digitaltwin.schemas import (
    CalibrationProfileResponse,
    CalibrationReviewRequest,
    CalibrationRunRequest,
    ForecastRefreshResponse,
    IrrigationEventCreate,
    IrrigationEventResponse,
    IrrigationRecommendationResponse,
    ParcelCreate,
    ParcelDeleteResponse,
    ParcelDetailResponse,
    ParcelResponse,
    RecommendationInline,
    SensorReadingCreate,
    SensorReadingDeleteResponse,
    SensorReadingInline,
    SensorReadingImportResponse,
    SensorReadingResponse,
    SimulationRequest,
    SimulationResponse,
    WeatherForecastResponse,
)
from agents.digitaltwin.services.calibration import (
    apply_calibration_profile,
    create_calibration_candidate,
)
from agents.digitaltwin.services.forecast import (
    list_current_forecasts,
    refresh_parcel_forecast,
)

router = APIRouter()


@router.get("/parcels", response_model=List[ParcelResponse])
async def list_parcels(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Parcel).order_by(Parcel.name))
    return result.scalars().all()


@router.post("/parcels", response_model=ParcelResponse, dependencies=[Depends(require_roles("administrator"))])
async def create_parcel(data: ParcelCreate, db: AsyncSession = Depends(get_db)):
    if data.project_id:
        # The project lives in MIS. Validate the cross-agent link at creation
        # time while keeping the twin usable for standalone research parcels.
        from agents.mis.models import Projet as ProjetModel

        project = await db.get(ProjetModel, data.project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="Linked project not found")

    parcel = Parcel(**data.model_dump())
    db.add(parcel)
    await db.commit()
    await db.refresh(parcel)
    return parcel


@router.delete(
    "/parcels/{parcel_id}",
    response_model=ParcelDeleteResponse,
    dependencies=[Depends(require_roles("administrator"))],
)
async def delete_parcel(parcel_id: int, db: AsyncSession = Depends(get_db)):
    """Remove a parcel, but only while nothing depends on it.

    Six tables carry a foreign key to twin_parcels and none declares a cascade.
    Rather than add one, this refuses with 409 while any child row exists and
    names the counts. The reasoning is that measurements are the expensive thing
    here: a season of readings and the calibrations fitted from them cannot be
    re-collected, so a single click must not be able to destroy them. Deleting
    the children is a deliberate, separate act — readings have their own delete
    route, and the rest are cheap to regenerate.

    Roles match create_parcel (administrator only), unlike the reading route
    which is open to whoever records data.
    """
    parcel = await db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail=f"Parcel {parcel_id} not found")

    # Ordered most-precious first, so the message leads with what actually
    # matters to protect. Labels are what the API calls these, not table names.
    dependants = (
        ("sensor readings", SensorReading),
        ("calibration profiles", CalibrationProfile),
        ("irrigation events", IrrigationEvent),
        ("recommendations", IrrigationRecommendation),
        ("weather forecasts", WeatherForecast),
        ("simulation scenarios", SimulationScenario),
    )
    blocking: list[str] = []
    for label, model in dependants:
        count_result = await db.execute(
            select(func.count()).select_from(model).where(model.parcel_id == parcel_id)
        )
        count = count_result.scalar_one()
        if count:
            blocking.append(f"{count} {label}")

    if blocking:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Parcel {parcel.code} still has {', '.join(blocking)}. "
                "Delete or archive them first — this refuses rather than "
                "cascading so field measurements cannot be lost by mistake."
            ),
        )

    code, name = parcel.code, parcel.name
    await db.delete(parcel)
    await db.commit()
    return ParcelDeleteResponse(deleted_id=parcel_id, code=code, name=name)


@router.get("/parcels/{parcel_id}", response_model=ParcelDetailResponse)
async def get_parcel(parcel_id: int, db: AsyncSession = Depends(get_db)):
    parcel = await db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    readings_result = await db.execute(
        select(SensorReading)
        .where(SensorReading.parcel_id == parcel_id)
        .order_by(SensorReading.recorded_at.desc())
        .limit(30)
    )
    recommendations_result = await db.execute(
        select(IrrigationRecommendation)
        .where(IrrigationRecommendation.parcel_id == parcel_id)
        .order_by(IrrigationRecommendation.generated_at.desc())
        .limit(5)
    )
    return ParcelDetailResponse(
        **{column.name: getattr(parcel, column.name) for column in Parcel.__table__.columns},
        latest_readings=[
            SensorReadingInline.model_validate(row)
            for row in readings_result.scalars().all()
        ],
        latest_recommendations=[
            RecommendationInline.model_validate(row)
            for row in recommendations_result.scalars().all()
        ],
    )


@router.get(
    "/parcels/{parcel_id}/forecasts",
    response_model=List[WeatherForecastResponse],
)
async def list_forecasts(
    parcel_id: int,
    days: int = Query(16, ge=1, le=16),
    db: AsyncSession = Depends(get_db),
):
    parcel = await db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    return await list_current_forecasts(db, parcel_id, days)


@router.post(
    "/parcels/{parcel_id}/forecasts/refresh",
    response_model=ForecastRefreshResponse,
    dependencies=[Depends(require_roles("researcher", "reviewer", "administrator"))],
)
async def refresh_forecast(
    parcel_id: int,
    db: AsyncSession = Depends(get_db),
):
    parcel = await db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    try:
        coverage = await refresh_parcel_forecast(db, parcel)
        await db.commit()
        return ForecastRefreshResponse(
            parcel_id=parcel_id,
            provider=coverage.provider,
            provider_model=coverage.provider_model,
            retrieved_at=coverage.retrieved_at,
            forecast_days=len(coverage.inputs),
            coverage_start=coverage.start_date,
            coverage_end=coverage.end_date,
            source_metadata={
                "forecast_is_modelled": True,
                "automated_control_enabled": False,
                "review_required_before_field_actuation": True,
            },
        )
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=502, detail=str(exc))


@router.get(
    "/parcels/{parcel_id}/readings",
    response_model=List[SensorReadingResponse],
)
async def list_readings(
    parcel_id: int,
    limit: int = Query(60, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    parcel = await db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    result = await db.execute(
        select(SensorReading)
        .where(SensorReading.parcel_id == parcel_id)
        .order_by(SensorReading.recorded_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.post(
    "/parcels/{parcel_id}/readings",
    response_model=SensorReadingResponse,
    dependencies=[Depends(require_roles("researcher", "reviewer", "administrator"))],
)
async def add_reading(
    parcel_id: int,
    data: SensorReadingCreate,
    db: AsyncSession = Depends(get_db),
):
    parcel = await db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    from agents.digitaltwin.agent import digital_twin_agent

    reading = await digital_twin_agent.ingest_reading(db, parcel_id, data.model_dump())
    await db.commit()
    await db.refresh(reading)
    # The commit comes first: downstream agents use independent sessions and
    # must never inspect an uncommitted field measurement.
    await digital_twin_agent.emit_event("events", Event(
        id=str(uuid4()),
        type="twin.reading_recorded",
        source_agent="digital_twin",
        payload={
            "parcel_id": parcel_id,
            "reading_id": reading.id,
            "reading": SensorReadingResponse.model_validate(reading).model_dump(mode="json"),
        },
    ))
    return reading


@router.delete(
    "/parcels/{parcel_id}/readings/{reading_id}",
    response_model=SensorReadingDeleteResponse,
    dependencies=[Depends(require_roles("researcher", "reviewer", "administrator"))],
)
async def delete_reading(
    parcel_id: int,
    reading_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Remove one sensor reading — the correction path for a mistyped measurement.

    Guarded with the same roles as adding a reading: whoever can record an
    observation must be able to retract it, because a wrong root-zone value keeps
    driving /recommend until a newer row replaces it.
    """
    reading = await db.get(SensorReading, reading_id)
    # Scope the lookup to the parcel in the path so
    # DELETE /parcels/1/readings/{id-belonging-to-2} cannot delete another
    # parcel's observation.
    if not reading or reading.parcel_id != parcel_id:
        raise HTTPException(
            status_code=404,
            detail=f"Reading {reading_id} not found on parcel {parcel_id}",
        )

    latest_result = await db.execute(
        select(SensorReading.id)
        .where(SensorReading.parcel_id == parcel_id)
        .order_by(SensorReading.recorded_at.desc())
        .limit(1)
    )
    was_latest = latest_result.scalar_one_or_none() == reading_id
    recorded_at = reading.recorded_at

    await db.delete(reading)
    await db.commit()

    remaining_result = await db.execute(
        select(func.count())
        .select_from(SensorReading)
        .where(SensorReading.parcel_id == parcel_id)
    )
    return SensorReadingDeleteResponse(
        parcel_id=parcel_id,
        deleted_id=reading_id,
        recorded_at=recorded_at,
        was_latest=was_latest,
        remaining=remaining_result.scalar_one(),
    )


@router.post(
    "/parcels/{parcel_id}/readings/import",
    response_model=SensorReadingImportResponse,
    dependencies=[Depends(require_roles("researcher", "reviewer", "administrator"))],
)
async def import_field_readings(
    parcel_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Import daily root-zone field readings from a validated CSV file."""
    parcel = await db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    try:
        payload = await file.read()
        if len(payload) > 5 * 1024 * 1024:
            raise ValueError("CSV import is limited to 5 MB")
        text = payload.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
    except (UnicodeDecodeError, csv.Error, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid CSV file: {exc}")

    required_columns = {
        "recorded_at",
        "soil_moisture_mm",
        "rainfall_mm",
        "evapotranspiration_mm",
    }
    headers = set(reader.fieldnames or [])
    missing_columns = sorted(required_columns - headers)
    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=(
                "CSV must contain daily root-zone water and weather columns: "
                + ", ".join(missing_columns)
            ),
        )

    created = 0
    updated = 0
    rejected = 0
    errors: list[str] = []
    for line_number, row in enumerate(reader, start=2):
        try:
            cleaned = {
                key: value.strip()
                for key, value in row.items()
                if key and value is not None and value.strip() != ""
            }
            data = SensorReadingCreate.model_validate({
                **cleaned,
                "data_origin": "field_import",
            })
            existing_result = await db.execute(
                select(SensorReading).where(
                    SensorReading.parcel_id == parcel_id,
                    SensorReading.recorded_at == data.recorded_at,
                    SensorReading.sensor_code == data.sensor_code,
                )
            )
            reading = existing_result.scalar_one_or_none()
            if reading:
                reading.soil_moisture_mm = data.soil_moisture_mm
                reading.rainfall_mm = data.rainfall_mm
                reading.evapotranspiration_mm = data.evapotranspiration_mm
                reading.temperature_c = data.temperature_c
                reading.quality_flag = data.quality_flag
                reading.data_origin = "field_import"
                updated += 1
            else:
                db.add(SensorReading(parcel_id=parcel_id, **data.model_dump()))
                created += 1
        except Exception as exc:
            rejected += 1
            if len(errors) < 20:
                errors.append(f"Row {line_number}: {exc}")

    if created or updated:
        await db.commit()
        # A bulk import may contain historical records. Only the newest accepted
        # reading is eligible to drive the current irrigation decision.
        latest_result = await db.execute(
            select(SensorReading)
            .where(SensorReading.parcel_id == parcel_id)
            .order_by(SensorReading.recorded_at.desc())
            .limit(1)
        )
        latest = latest_result.scalar_one_or_none()
        if latest:
            from agents.digitaltwin.agent import digital_twin_agent

            await digital_twin_agent.emit_event("events", Event(
                id=str(uuid4()),
                type="twin.reading_recorded",
                source_agent="digital_twin",
                payload={
                    "parcel_id": parcel_id,
                    "reading_id": latest.id,
                    "reading": SensorReadingResponse.model_validate(latest).model_dump(mode="json"),
                },
            ))
    else:
        await db.rollback()

    return SensorReadingImportResponse(
        parcel_id=parcel_id,
        created=created,
        updated=updated,
        rejected=rejected,
        errors=errors,
    )


@router.get(
    "/parcels/{parcel_id}/irrigation-events",
    response_model=List[IrrigationEventResponse],
)
async def list_irrigation_events(
    parcel_id: int,
    limit: int = Query(60, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    parcel = await db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    result = await db.execute(
        select(IrrigationEvent)
        .where(IrrigationEvent.parcel_id == parcel_id)
        .order_by(IrrigationEvent.occurred_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.post(
    "/parcels/{parcel_id}/irrigation-events",
    response_model=IrrigationEventResponse,
    dependencies=[Depends(require_roles("researcher", "reviewer", "administrator"))],
)
async def record_irrigation_event(
    parcel_id: int,
    data: IrrigationEventCreate,
    db: AsyncSession = Depends(get_db),
):
    parcel = await db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    if data.recommendation_id is not None:
        recommendation = await db.get(IrrigationRecommendation, data.recommendation_id)
        if not recommendation:
            raise HTTPException(status_code=404, detail="Irrigation recommendation not found")
        if recommendation.parcel_id != parcel_id:
            raise HTTPException(status_code=422, detail="Recommendation belongs to another parcel")
        if not recommendation.is_validated:
            raise HTTPException(status_code=409, detail="Recommendation must be approved before logging its application")

    event = IrrigationEvent(parcel_id=parcel_id, **data.model_dump())
    db.add(event)
    await db.commit()
    await db.refresh(event)
    if event.recommendation_id is not None:
        from agents.digitaltwin.agent import digital_twin_agent

        await digital_twin_agent.emit_event("events", Event(
            id=str(uuid4()),
            type="irrigation.applied",
            source_agent="digital_twin",
            payload={
                "parcel_id": parcel_id,
                "recommendation_id": event.recommendation_id,
                "irrigation_event_id": event.id,
                "amount_mm": event.amount_mm,
            },
        ))
    return event


@router.post(
    "/parcels/{parcel_id}/calibrations/run",
    response_model=CalibrationProfileResponse,
    dependencies=[Depends(require_roles("researcher", "reviewer", "administrator"))],
)
async def run_calibration(
    parcel_id: int,
    data: CalibrationRunRequest,
    db: AsyncSession = Depends(get_db),
):
    parcel = await db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    try:
        profile = await create_calibration_candidate(
            db=db,
            parcel=parcel,
            start_date=data.start_date,
            end_date=data.end_date,
            min_observations=data.min_observations,
        )
        await db.commit()
        await db.refresh(profile)
        return profile
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))


@router.get(
    "/parcels/{parcel_id}/calibrations",
    response_model=List[CalibrationProfileResponse],
)
async def list_calibrations(
    parcel_id: int,
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    parcel = await db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    result = await db.execute(
        select(CalibrationProfile)
        .where(CalibrationProfile.parcel_id == parcel_id)
        .order_by(CalibrationProfile.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.post(
    "/calibrations/{profile_id}/apply",
    response_model=CalibrationProfileResponse,
    dependencies=[Depends(require_roles("reviewer", "administrator"))],
)
async def apply_calibration(
    profile_id: int,
    data: CalibrationReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        profile = await apply_calibration_profile(
            db=db,
            profile_id=profile_id,
            reviewed_by=data.reviewed_by,
        )
        await db.commit()
        await db.refresh(profile)
        return profile
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/parcels/{parcel_id}/recommend",
    response_model=IrrigationRecommendationResponse,
    dependencies=[Depends(require_roles("researcher", "reviewer", "administrator"))],
)
async def generate_recommendation(
    parcel_id: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        from agents.digitaltwin.agent import digital_twin_agent

        recommendation = await digital_twin_agent.generate_recommendation(db, parcel_id)
        await db.commit()
        await db.refresh(recommendation)
        parcel = await db.get(Parcel, parcel_id)
        await digital_twin_agent.emit_event("events", Event(
            id=str(uuid4()),
            type="twin.recommendation_generated",
            source_agent="digital_twin",
            payload={
                "parcel_id": parcel_id,
                "recommendation_id": recommendation.id,
                "recommended_irrigation_mm": recommendation.recommended_irrigation_mm,
                "generation_mode": recommendation.generation_mode,
                "project_id": parcel.project_id if parcel else None,
                "parcel_name": parcel.name if parcel else None,
                "review_required": True,
            },
        ))
        return recommendation
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/recommendations",
    response_model=List[IrrigationRecommendationResponse],
)
async def list_recommendations(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(IrrigationRecommendation)
        .order_by(IrrigationRecommendation.generated_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.patch(
    "/recommendations/{recommendation_id}/approve",
    response_model=IrrigationRecommendationResponse,
)
async def approve_recommendation(
    recommendation_id: int,
    user: User = Depends(require_roles("reviewer", "administrator")),
    db: AsyncSession = Depends(get_db),
):
    """Record expert approval; this does not command any irrigation hardware."""
    recommendation = await db.get(IrrigationRecommendation, recommendation_id)
    if not recommendation:
        raise HTTPException(status_code=404, detail="Irrigation recommendation not found")
    if recommendation.is_validated:
        raise HTTPException(status_code=400, detail="Recommendation has already been approved")

    recommendation.is_validated = True
    recommendation.validated_by = user.email or user.id
    await db.commit()
    await db.refresh(recommendation)
    return recommendation


@router.post(
    "/parcels/{parcel_id}/simulate",
    response_model=SimulationResponse,
    dependencies=[Depends(require_roles("researcher", "reviewer", "administrator"))],
)
async def run_legacy_simulation(
    parcel_id: int,
    data: SimulationRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        from agents.digitaltwin.agent import digital_twin_agent

        scenario = await digital_twin_agent.run_scenario(db, parcel_id, data.model_dump())
        await db.commit()
        await db.refresh(scenario)
        return scenario
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
