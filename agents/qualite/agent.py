# -*- coding: utf-8 -*-
"""Qualité Agent – Data quality validation and GDPR compliance.

Adapted from Friend 1's QualiteAgent to use the monorepo's shared BaseAgent.
"""
from __future__ import annotations
import re
from datetime import datetime
from typing import Optional
from uuid import uuid4

from shared.base_agent import BaseAgent
from shared.outbox import enqueue_event, outbox_dispatcher
from shared.schemas import Event, AgentAction, ActionResult
from agents.qualite.schemas import RapportQualite, NiveauQualite


class QualiteAgent(BaseAgent):
    """Validates data quality for projects, personnel, equipment, and budgets."""

    name = "qualite"
    permissions = ["qual.read", "qual.write"]
    requires_human_approval = []

    def __init__(self):
        super().__init__()
        # Reports are now persisted in the qualite_rapports table; the previous
        # in-memory _rapports list is gone (reports survived no restart).

    async def _setup_subscriptions(self):
        """Subscribe to the fanout stream and handle validation requests."""
        await self._subscribe("events", self._on_bus_event)

    async def _on_bus_event(self, event: Event) -> None:
        """Bus callback — only act on explicit quality validation requests."""
        if event.type == "qualite.validation_demandee":
            await self.handle_event(event)
        elif event.type == "twin.reading_recorded":
            await self._validate_twin_reading(event)

    async def _validate_twin_reading(self, event: Event) -> None:
        """Compute the reading's quality flag and gate automatic advice on it.

        The flag used to be echoed straight from the client (always "ok" unless
        someone typed otherwise). Now the qualité agent runs the physical
        checks in services/anomaly.py — impossible values are errors,
        extreme-but-possible ones are suspects — and writes the verdict back
        onto the reading row. Only "ok" emits twin.reading_validated, so the
        auto-recommendation and the calibrator (which filters on quality_flag)
        never consume data a human has not cleared.
        """
        payload = event.payload
        parcel_id = payload.get("parcel_id")
        reading_id = payload.get("reading_id")
        reading = payload.get("reading") or {}

        # Read current persisted state, not an old queued snapshot. A reviewed
        # decision must survive duplicate delivery of its ingestion event.
        from shared.database import AsyncSessionLocal
        from agents.digitaltwin.models import SensorReading
        from agents.digitaltwin.schemas import SensorReadingResponse
        async with AsyncSessionLocal() as db:
            current = await db.get(SensorReading, reading_id) if isinstance(reading_id, int) else None
            if current is not None:
                if current.review_status != "pending_validation":
                    return
                reading = SensorReadingResponse.model_validate(current).model_dump(mode="json")

        issues: list[str] = []
        if not isinstance(parcel_id, int) or not isinstance(reading_id, int):
            issues.append("[error] missing parcel or reading identifier")

        verdict = None
        if not issues:
            verdict = await self._assess_reading(parcel_id, reading_id, reading)
            issues = verdict.issues

        # Persist the verdict and the next event in one transaction so a
        # quality-approved reading can never be stranded without triggering
        # the recommendation workflow.
        from shared.database import AsyncSessionLocal
        from agents.digitaltwin.models import SensorReading
        from agents.qualite.models import MeasurementReviewDB

        async with AsyncSessionLocal() as db:
            row = await db.get(SensorReading, reading_id) if isinstance(reading_id, int) else None
            if row is None:
                raise ValueError(f"Reading {reading_id!r} no longer exists")
            if verdict is not None:
                row.quality_flag = verdict.flag
            row.quality_issues = issues
            row.review_status = "pending" if issues else "not_required"
            if issues:
                db.add(MeasurementReviewDB(
                    id=str(uuid4()), reading_id=str(reading_id), parcel_id=str(parcel_id),
                    status="pending", quality_flag=verdict.flag if verdict else "error", issues=issues,
                ))
            await enqueue_event(db, "events", Event(
                id=str(uuid4()),
                type="twin.reading_validated" if not issues else "twin.reading_rejected",
                source_agent=self.name,
                payload={
                    "parcel_id": parcel_id,
                    "reading_id": reading_id,
                    "quality_flag": verdict.flag if verdict else "error",
                    "issues": issues,
                    "review_required": True,
                },
            ))
            await db.commit()
        outbox_dispatcher.notify()

    async def _assess_reading(self, parcel_id: int, reading_id: int, reading: dict):
        """Load the context the physical checks need, then run them.

        Context: the parcel's field capacity (saturation ceiling), the previous
        reading on the same parcel (rate-of-change baseline) and same-day
        logged irrigation (part of the plausible-rise budget). Opening one
        short session here is safe — the reading was committed before the
        event was emitted, so there is no lock to wait on.
        """
        from sqlalchemy import select, func
        from shared.database import AsyncSessionLocal
        from agents.digitaltwin.models import Parcel, SensorReading, IrrigationEvent
        from agents.qualite.services.anomaly import ReadingVerdict, verdict_for

        async with AsyncSessionLocal() as db:
            parcel = await db.get(Parcel, parcel_id)
            field_capacity = parcel.field_capacity_mm if parcel else None
            observed_at = datetime.fromisoformat(str(reading["recorded_at"]))

            previous_row = (
                await db.execute(
                    select(SensorReading)
                    .where(
                        SensorReading.parcel_id == parcel_id,
                        SensorReading.id != reading_id,
                        SensorReading.recorded_at < observed_at,
                        SensorReading.quality_flag == "ok",
                        SensorReading.review_status.in_(["not_required", "accepted", "corrected"]),
                    )
                    .order_by(SensorReading.recorded_at.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()
            previous = (
                {
                    "soil_moisture_mm": previous_row.soil_moisture_mm,
                    "recorded_at": previous_row.recorded_at.isoformat()
                    if previous_row.recorded_at else None,
                }
                if previous_row else None
            )

            irrigation_same_day = 0.0
            if previous is not None and reading.get("recorded_at"):
                try:
                    day = datetime.fromisoformat(str(reading["recorded_at"])).date()
                    irrigation_same_day = float(
                        (
                            await db.execute(
                                select(func.coalesce(func.sum(IrrigationEvent.amount_mm), 0.0)).where(
                                    IrrigationEvent.parcel_id == parcel_id,
                                    func.date(IrrigationEvent.occurred_at) == day,
                                )
                            )
                        ).scalar_one()
                    )
                except (TypeError, ValueError):
                    irrigation_same_day = 0.0

            return verdict_for(
                reading,
                field_capacity_mm=field_capacity,
                previous=previous,
                irrigation_same_day_mm=irrigation_same_day,
            )

    async def _persist_reading_flag(self, reading_id: int, flag: str) -> None:
        """Write the computed verdict onto the reading row so every consumer
        (recommendation gate, calibrator, UI badges) sees the same truth."""
        from shared.database import AsyncSessionLocal
        from agents.digitaltwin.models import SensorReading

        async with AsyncSessionLocal() as db:
            row = await db.get(SensorReading, reading_id)
            if row is not None:
                row.quality_flag = flag
                await db.commit()

    async def handle_event(self, event: Event) -> Optional[AgentAction]:
        """Handle quality validation events."""
        print(f"[{self.name}] Event received: {event.type}")
        entite_type = event.payload.get("entite_type")
        entite_id = event.payload.get("entite_id")
        data = event.payload.get("data", {})

        rapport = None
        if entite_type == "projet":
            rapport = self.valider_projet(entite_id, data)
        elif entite_type == "personnel":
            rapport = self.valider_personnel(entite_id, data)
        elif entite_type == "equipement":
            rapport = self.valider_equipement(entite_id, data)
        elif entite_type == "budget":
            rapport = self.valider_budget(entite_id, data)

        if rapport:
            await self._persist_rapport(rapport)

        return None

    async def execute_action(self, action: AgentAction) -> ActionResult:
        return ActionResult(
            action_id=action.id,
            status="completed",
            result_data={"message": "Action executed by QualiteAgent"},
        )

    # ── Validation Methods ────────────────────────────────────────────

    def valider_projet(self, entite_id: str, data: dict) -> RapportQualite:
        problemes = []
        if not data.get("responsable"):
            problemes.append("Responsable non défini.")
        if not data.get("budget_alloue") or data.get("budget_alloue", 0) == 0:
            problemes.append("Budget alloué nul ou manquant.")
        if not data.get("date_fin_prevue"):
            problemes.append("Date de fin prévue non définie.")
        if not data.get("description"):
            problemes.append("Description manquante.")

        niveau = self._calculer_niveau(problemes)
        return RapportQualite(entite_type="projet", entite_id=entite_id, niveau=niveau, problemes=problemes)

    def valider_personnel(self, entite_id: str, data: dict) -> RapportQualite:
        problemes = []
        conforme_rgpd = True

        if not data.get("email"):
            problemes.append("Email manquant.")
            conforme_rgpd = False
        elif not re.match(r"^[\w\.\-]+@[\w\.\-]+\.\w+$", data.get("email", "")):
            problemes.append("Format email invalide.")
            conforme_rgpd = False
        if not data.get("role"):
            problemes.append("Rôle non défini.")
        if not data.get("nom") or not data.get("prenom"):
            problemes.append("Nom ou prénom manquant.")
            conforme_rgpd = False
        if not data.get("competences"):
            problemes.append("Aucune compétence renseignée.")

        niveau = self._calculer_niveau(problemes)
        return RapportQualite(
            entite_type="personnel", entite_id=entite_id, niveau=niveau,
            problemes=problemes, conforme_rgpd=conforme_rgpd,
        )

    def valider_equipement(self, entite_id: str, data: dict) -> RapportQualite:
        problemes = []
        if not data.get("localisation"):
            problemes.append("Localisation non définie.")
        if not data.get("responsable_id"):
            problemes.append("Aucun responsable assigné.")
        if data.get("valeur_estimee", 0) == 0:
            problemes.append("Valeur estimée nulle.")
        if not data.get("date_acquisition"):
            problemes.append("Date d'acquisition manquante.")

        niveau = self._calculer_niveau(problemes)
        return RapportQualite(entite_type="equipement", entite_id=entite_id, niveau=niveau, problemes=problemes)

    def valider_budget(self, entite_id: str, data: dict) -> RapportQualite:
        problemes = []
        if not data.get("projet_id"):
            problemes.append("Projet associé manquant.")
        alloue = data.get("montant_alloue", 0)
        depense = data.get("montant_depense", 0)
        if alloue == 0:
            problemes.append("Montant alloué nul.")
        if depense > alloue:
            problemes.append(f"Dépenses ({depense}) dépassent le budget alloué ({alloue}).")
        if not data.get("date_debut"):
            problemes.append("Date de début manquante.")

        niveau = self._calculer_niveau(problemes)
        return RapportQualite(entite_type="budget", entite_id=entite_id, niveau=niveau, problemes=problemes)

    # ── Utilities ─────────────────────────────────────────────────────

    def _calculer_niveau(self, problemes: list[str]) -> NiveauQualite:
        if len(problemes) == 0:
            return "conforme"
        elif len(problemes) <= 2:
            return "avertissement"
        else:
            return "non_conforme"

    # ── Persistence ────────────────────────────────────────────────────
    #
    # Reports are persisted to the qualite_rapports table so they survive
    # restarts. Both the validation router (which holds a request DB session)
    # and the event path (which opens its own short session) funnel through here.

    async def _persist_rapport(self, rapport: RapportQualite, db=None) -> RapportQualite:
        from agents.qualite.models import RapportQualiteDB

        owns_session = db is None
        if owns_session:
            from shared.database import AsyncSessionLocal
            db = AsyncSessionLocal()
        try:
            db.add(RapportQualiteDB(
                id=rapport.id,
                entite_type=rapport.entite_type,
                entite_id=rapport.entite_id,
                niveau=rapport.niveau,
                problemes=rapport.problemes,
                conforme_rgpd=rapport.conforme_rgpd,
                timestamp=rapport.timestamp,
            ))
            await db.commit()
        finally:
            if owns_session:
                await db.close()
        return rapport

    async def get_rapports(self, db=None) -> list[RapportQualite]:
        from agents.qualite.models import RapportQualiteDB
        from sqlalchemy import select

        owns_session = db is None
        if owns_session:
            from shared.database import AsyncSessionLocal
            db = AsyncSessionLocal()
        try:
            result = await db.execute(select(RapportQualiteDB).order_by(RapportQualiteDB.timestamp))
            rows = result.scalars().all()
        finally:
            if owns_session:
                await db.close()
        return [RapportQualite(
            id=r.id, entite_type=r.entite_type, entite_id=r.entite_id,
            niveau=r.niveau, problemes=r.problemes,
            timestamp=r.timestamp, conforme_rgpd=r.conforme_rgpd,
        ) for r in rows]

    async def get_rapport_par_entite(self, entite_id: str, db=None) -> list[RapportQualite]:
        from agents.qualite.models import RapportQualiteDB
        from sqlalchemy import select

        owns_session = db is None
        if owns_session:
            from shared.database import AsyncSessionLocal
            db = AsyncSessionLocal()
        try:
            result = await db.execute(
                select(RapportQualiteDB)
                .where(RapportQualiteDB.entite_id == entite_id)
                .order_by(RapportQualiteDB.timestamp)
            )
            rows = result.scalars().all()
        finally:
            if owns_session:
                await db.close()
        return [RapportQualite(
            id=r.id, entite_type=r.entite_type, entite_id=r.entite_id,
            niveau=r.niveau, problemes=r.problemes,
            timestamp=r.timestamp, conforme_rgpd=r.conforme_rgpd,
        ) for r in rows]

    async def get_stats(self, db=None) -> dict:
        rapports = await self.get_rapports(db)
        conformes = len([r for r in rapports if r.niveau == "conforme"])
        avertissements = len([r for r in rapports if r.niveau == "avertissement"])
        non_conformes = len([r for r in rapports if r.niveau == "non_conforme"])
        return {
            "total_rapports": len(rapports),
            "conformes": conformes,
            "avertissements": avertissements,
            "non_conformes": non_conformes,
        }


qualite_agent = QualiteAgent()
