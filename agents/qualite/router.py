# -*- coding: utf-8 -*-
"""Qualité Router – validation endpoints for all entity types."""
from __future__ import annotations
import json
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from agents.qualite.schemas import RapportQualite, DemandeValidation
from agents.qualite.schemas import MeasurementReviewDecision, MeasurementReviewResponse
from agents.qualite.agent import qualite_agent
from agents.qualite.models import MeasurementReviewDB
from agents.digitaltwin.models import SensorReading, IrrigationRecommendation
from agents.digitaltwin.schemas import SensorReadingCreate, SensorReadingResponse
from agents.mis.models import (
    Projet as ProjetModel,
    Personnel as PersonnelModel,
    Equipement as EquipementModel,
    Budget as BudgetModel,
)
from shared.database import get_db
from shared.outbox import enqueue_event, outbox_dispatcher
from shared.schemas import Event
from shared.security import User, require_roles

router = APIRouter(tags=["Qualité"])


def _review_response(review: MeasurementReviewDB) -> dict:
    return {
        "id": review.id, "reading_id": int(review.reading_id), "parcel_id": int(review.parcel_id),
        "status": review.status, "quality_flag": review.quality_flag,
        "issues": review.issues or [], "annotation": review.annotation,
        "reviewer_id": review.reviewer_id, "reviewed_at": review.reviewed_at,
        "correction": review.correction, "created_at": review.created_at,
    }


@router.get("/status")
async def get_status(db: AsyncSession = Depends(get_db)) -> dict:
    stats = await qualite_agent.get_stats(db)
    return {"agent": qualite_agent.name, "statut": "actif", **stats}


@router.get("/rapports", response_model=list[RapportQualite])
async def get_rapports(db: AsyncSession = Depends(get_db)) -> list[RapportQualite]:
    return await qualite_agent.get_rapports(db)


@router.get("/measurement-reviews", response_model=list[MeasurementReviewResponse])
async def list_measurement_reviews(
    status: str = "pending",
    db: AsyncSession = Depends(get_db),
):
    query = select(MeasurementReviewDB).order_by(MeasurementReviewDB.created_at.desc())
    if status != "all":
        query = query.where(MeasurementReviewDB.status == status)
    rows = (await db.execute(query)).scalars().all()
    return [_review_response(row) for row in rows]


@router.patch("/measurement-reviews/{review_id}", response_model=MeasurementReviewResponse)
async def decide_measurement_review(
    review_id: str,
    data: MeasurementReviewDecision,
    user: User = Depends(require_roles("reviewer", "administrator")),
    db: AsyncSession = Depends(get_db),
):
    """Accept, reject, annotate, or correct one quarantined field value."""
    review = await db.get(MeasurementReviewDB, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Measurement review not found")
    if review.status in {"accepted", "rejected", "corrected"} and data.action != "annotate":
        raise HTTPException(status_code=409, detail="This measurement review has already been decided")

    reading = await db.get(SensorReading, int(review.reading_id))
    if reading is None:
        raise HTTPException(status_code=404, detail="The reviewed measurement no longer exists")
    linked = await db.scalar(select(IrrigationRecommendation.id).where(
        IrrigationRecommendation.source_reading_id == reading.id))
    if linked is not None and data.action == "correct":
        raise HTTPException(status_code=409, detail="This measurement already supports recorded advice. Add a new measurement to preserve its provenance.")
    reviewer = user.email or user.id
    review.annotation = data.annotation or review.annotation
    review.reviewer_id = reviewer
    review.reviewed_at = datetime.utcnow()
    reading.reviewed_by = reviewer
    reading.reviewed_at = review.reviewed_at
    reading.review_notes = review.annotation

    if data.action == "annotate":
        await db.commit()
        await db.refresh(review)
        return _review_response(review)

    if data.action == "reject":
        review.status = "rejected"
        reading.review_status = "rejected"
        await db.commit()
        await db.refresh(review)
        return _review_response(review)

    if data.action == "accept" and reading.quality_flag == "error":
        raise HTTPException(status_code=422, detail="An erroneous measurement must be corrected or rejected, not accepted unchanged.")

    if data.action == "correct":
        if not data.correction:
            raise HTTPException(status_code=422, detail="A correction payload is required")
        before = SensorReadingResponse.model_validate(reading).model_dump(mode="json")
        accepted_keys = {
            "recorded_at", "soil_moisture_mm", "rainfall_mm", "evapotranspiration_mm", "temperature_c",
        }
        unknown = set(data.correction) - accepted_keys
        if unknown:
            raise HTTPException(status_code=422, detail="Unsupported correction fields: " + ", ".join(sorted(unknown)))
        try:
            candidate = SensorReadingCreate.model_validate({**before, **data.correction})
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=json.loads(exc.json(include_url=False))) from exc
        verdict = await qualite_agent._assess_reading(reading.parcel_id, reading.id, candidate.model_dump(mode="json"))
        if verdict.flag == "error":
            raise HTTPException(status_code=422, detail="Correction still contains an error: " + "; ".join(verdict.issues))
        for key in accepted_keys:
            if key in data.correction:
                setattr(reading, key, getattr(candidate, key))
        review.status = "corrected"
        review.correction = {"before": before, "after": data.correction}
        reading.review_status = "corrected"
        reading.quality_flag = "ok"
    else:
        review.status = "accepted"
        reading.review_status = "accepted"
        reading.quality_flag = "ok"

    await enqueue_event(db, "events", Event(
        id=str(uuid4()), type="twin.reading_validated", source_agent="qualite",
        payload={
            "parcel_id": reading.parcel_id, "reading_id": reading.id, "quality_flag": "ok",
            "issues": review.issues or [], "review_required": False, "reviewer": reviewer,
        },
    ))
    await db.commit()
    await db.refresh(review)
    outbox_dispatcher.notify()
    return _review_response(review)


@router.get("/rapports/{entite_id}", response_model=list[RapportQualite])
async def get_rapport_entite(entite_id: str, db: AsyncSession = Depends(get_db)) -> list[RapportQualite]:
    rapports = await qualite_agent.get_rapport_par_entite(entite_id, db)
    if not rapports:
        raise HTTPException(status_code=404, detail="Aucun rapport pour cette entité")
    return rapports


@router.post("/valider/projet/{projet_id}", response_model=RapportQualite)
async def valider_projet(projet_id: str, db: AsyncSession = Depends(get_db)) -> RapportQualite:
    projet = await db.get(ProjetModel, projet_id)
    if projet is None:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    rapport = qualite_agent.valider_projet(projet_id, projet.__dict__)
    await qualite_agent._persist_rapport(rapport, db)
    return rapport


@router.post("/valider/personnel/{personnel_id}", response_model=RapportQualite)
async def valider_personnel(personnel_id: str, db: AsyncSession = Depends(get_db)) -> RapportQualite:
    personnel = await db.get(PersonnelModel, personnel_id)
    if personnel is None:
        raise HTTPException(status_code=404, detail="Personnel introuvable")
    data = personnel.__dict__.copy()
    data["competences"] = json.loads(data["competences"])
    rapport = qualite_agent.valider_personnel(personnel_id, data)
    await qualite_agent._persist_rapport(rapport, db)
    return rapport


@router.post("/valider/equipement/{equipement_id}", response_model=RapportQualite)
async def valider_equipement(equipement_id: str, db: AsyncSession = Depends(get_db)) -> RapportQualite:
    equipement = await db.get(EquipementModel, equipement_id)
    if equipement is None:
        raise HTTPException(status_code=404, detail="Équipement introuvable")
    rapport = qualite_agent.valider_equipement(equipement_id, equipement.__dict__)
    await qualite_agent._persist_rapport(rapport, db)
    return rapport


@router.post("/valider/budget/{budget_id}", response_model=RapportQualite)
async def valider_budget(budget_id: str, db: AsyncSession = Depends(get_db)) -> RapportQualite:
    budget = await db.get(BudgetModel, budget_id)
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget introuvable")
    rapport = qualite_agent.valider_budget(budget_id, budget.__dict__)
    await qualite_agent._persist_rapport(rapport, db)
    return rapport
