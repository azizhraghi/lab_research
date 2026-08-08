# -*- coding: utf-8 -*-
"""Orchestrator Agent – Central event routing and alerting.

Adapted from Friend 1's OrchestratorAgent to use the monorepo's shared BaseAgent.
Keeps the full routing table and alert system.
"""
from __future__ import annotations
from typing import Optional

from shared.base_agent import BaseAgent
from shared.schemas import Event, AgentAction, ActionResult
from agents.orchestrateur.schemas import Alerte, HistoriqueEvenement


class OrchestratorAgent(BaseAgent):
    """Routes events to the correct handlers and generates alerts."""

    name = "orchestrateur"
    permissions = ["orch.read", "orch.write", "orch.route"]
    requires_human_approval = []

    def __init__(self):
        super().__init__()
        # Alerts + history are now persisted (orch_alertes / orch_historique) so
        # they survive restarts. The previous in-memory lists are gone.

        # Routing table: event type → list of handler functions
        self._regles: dict[str, list] = {
            # MIS
            "projet.created":                [self._verifier_projet],
            "projet.statut_change":          [self._verifier_statut_projet],
            "budget.depense":                [self._verifier_seuil_budget],
            "equipement.etat_change":        [self._verifier_equipement],
            "personnel.indisponible":        [self._verifier_personnel],
            # Veille Scientifique
            "veille.article_trouve":         [self._notifier_chercheurs],
            "veille.resume_genere":          [self._declencher_validation_qualite],
            # Bibliométrie
            "bibliometrie.profil_mis_a_jour": [self._synchroniser_mis],
            "bibliometrie.cv_genere":        [self._archiver_document],
            # Simulation
            "simulation.terminee":           [self._declencher_optimisation],
            "simulation.calibration_ok":     [self._archiver_resultats],
            # Optimisation
            "optimisation.strategie_calculee": [self._notifier_strategie],
            "optimisation.contrainte_violee":  [self._alerte_contrainte],
            # Qualité
            "qualite.anomalie_detectee":     [self._suspendre_projet],
            "qualite.validation_ok":         [self._marquer_conforme],
        }

    async def _setup_subscriptions(self):
        """Subscribe to the fanout stream — the orchestrator routes every event."""
        await self._subscribe("events", self._on_bus_event)

    async def _on_bus_event(self, event: Event) -> None:
        """Bus callback — route the event through the rule table + persist."""
        try:
            await self.handle_event(event)
        except Exception as e:
            print(f"[{self.name}] Error handling {event.type}: {e}")

    async def handle_event(self, event: Event) -> Optional[AgentAction]:
        """Route an event through matching rules and persist the result."""
        print(f"[{self.name}] Event received: {event.type} from {event.source_agent}")

        # Run each matching rule exactly once and keep the Alertes it returns.
        # Each Alerte carries a uuid generated at creation, so we must persist
        # these same objects (not re-invoke the handler) to keep history→alert
        # id references consistent.
        handlers = self._regles.get(event.type, [])
        generated_alertes: list[Alerte] = []
        for handler in handlers:
            alerte = await handler(event)
            if alerte:
                generated_alertes.append(alerte)

        from shared.database import AsyncSessionLocal
        from agents.orchestrateur.models import AlerteDB, HistoriqueEvenementDB
        from uuid import uuid4

        async with AsyncSessionLocal() as db:
            for alerte in generated_alertes:
                db.add(AlerteDB(
                    id=alerte.id, niveau=alerte.niveau, message=alerte.message,
                    source_evenement=alerte.source_evenement,
                    timestamp=alerte.timestamp, resolue=False,
                ))
            db.add(HistoriqueEvenementDB(
                id=str(uuid4()),
                type_evenement=event.type,
                source_agent=event.source_agent,
                payload=event.payload,
                alertes_generees=[a.id for a in generated_alertes],
            ))
            await db.commit()
        return None

    async def execute_action(self, action: AgentAction) -> ActionResult:
        return ActionResult(
            action_id=action.id,
            status="completed",
            result_data={"message": "Action executed by OrchestratorAgent"},
        )

    # ── MIS Rules ─────────────────────────────────────────────────────

    async def _verifier_projet(self, event: Event) -> Alerte | None:
        payload = event.payload
        if not payload.get("responsable"):
            return Alerte(
                niveau="rouge",
                message=f"Projet '{payload.get('nom', '?')}' créé sans responsable.",
                source_evenement=event.type,
            )
        if payload.get("budget_alloue", 0) == 0:
            return Alerte(
                niveau="orange",
                message=f"Projet '{payload.get('nom', '?')}' créé avec un budget nul.",
                source_evenement=event.type,
            )
        return None

    async def _verifier_statut_projet(self, event: Event) -> Alerte | None:
        if event.payload.get("statut") == "suspendu":
            return Alerte(
                niveau="orange",
                message=f"Projet '{event.payload.get('nom', '?')}' suspendu.",
                source_evenement=event.type,
            )
        return None

    async def _verifier_seuil_budget(self, event: Event) -> Alerte | None:
        alloue = event.payload.get("montant_alloue", 0)
        depense = event.payload.get("montant_depense", 0)
        if alloue == 0:
            return None
        ratio = depense / alloue
        if ratio >= 1.0:
            return Alerte(
                niveau="critique",
                message=f"Budget dépassé à {ratio*100:.1f}% — projet {event.payload.get('projet_id', '?')}.",
                source_evenement=event.type,
            )
        if ratio >= 0.8:
            return Alerte(
                niveau="orange",
                message=f"Budget à {ratio*100:.1f}% — projet {event.payload.get('projet_id', '?')}.",
                source_evenement=event.type,
            )
        return None

    async def _verifier_equipement(self, event: Event) -> Alerte | None:
        etat = event.payload.get("etat")
        nom = event.payload.get("nom", "?")
        if etat == "en_maintenance":
            return Alerte(niveau="info", message=f"Équipement '{nom}' en maintenance.", source_evenement=event.type)
        if etat == "indisponible":
            return Alerte(niveau="orange", message=f"Équipement '{nom}' indisponible.", source_evenement=event.type)
        return None

    async def _verifier_personnel(self, event: Event) -> Alerte | None:
        return Alerte(
            niveau="info",
            message=f"Personnel '{event.payload.get('nom', '?')}' indisponible — vérifier projets impactés.",
            source_evenement=event.type,
        )

    # ── Veille Rules ──────────────────────────────────────────────────

    async def _notifier_chercheurs(self, event: Event) -> Alerte | None:
        print(f"[{self.name}] Nouvel article : {event.payload.get('titre', '?')} — chercheurs notifiés.")
        return None

    async def _declencher_validation_qualite(self, event: Event) -> Alerte | None:
        print(f"[{self.name}] Résumé généré → déclenchement validation Qualité.")
        return None

    # ── Bibliométrie Rules ────────────────────────────────────────────

    async def _synchroniser_mis(self, event: Event) -> Alerte | None:
        print(f"[{self.name}] Profil mis à jour → synchronisation MIS.")
        return None

    async def _archiver_document(self, event: Event) -> Alerte | None:
        print(f"[{self.name}] CV généré → archivage MIS.")
        return None

    # ── Simulation Rules ──────────────────────────────────────────────

    async def _declencher_optimisation(self, event: Event) -> Alerte | None:
        print(f"[{self.name}] Simulation terminée → déclenchement Optimisation automatique.")
        return None

    async def _archiver_resultats(self, event: Event) -> Alerte | None:
        print(f"[{self.name}] Calibration OK → archivage résultats dans MIS.")
        return None

    # ── Optimisation Rules ────────────────────────────────────────────

    async def _notifier_strategie(self, event: Event) -> Alerte | None:
        print(f"[{self.name}] Stratégie calculée : {event.payload.get('strategie', '?')} — notification équipe.")
        return None

    async def _alerte_contrainte(self, event: Event) -> Alerte | None:
        return Alerte(
            niveau="critique",
            message=f"Contrainte violée en optimisation : {event.payload.get('contrainte', '?')}.",
            source_evenement=event.type,
        )

    # ── Qualité Rules ─────────────────────────────────────────────────

    async def _suspendre_projet(self, event: Event) -> Alerte | None:
        return Alerte(
            niveau="critique",
            message=f"Anomalie détectée par Qualité — projet {event.payload.get('projet_id', '?')} suspendu.",
            source_evenement=event.type,
        )

    async def _marquer_conforme(self, event: Event) -> Alerte | None:
        print(f"[{self.name}] Validation Qualité OK → données marquées conformes RGPD.")
        return None

    # ── Accessors (for API endpoints) ─────────────────────────────────
    #
    # All reads/writes hit the DB so state survives restarts. Each opens its
    # own short session (the router endpoints are sync `def` historically, but
    # we make them async and await these).

    async def get_alertes(self, resolues: bool = False) -> list[Alerte]:
        from sqlalchemy import select
        from shared.database import AsyncSessionLocal
        from agents.orchestrateur.models import AlerteDB

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(AlerteDB).where(AlerteDB.resolue == resolues)
            )
            rows = result.scalars().all()
        # Arrival order newest-last in the table; keep that so the frontend's
        # existing `.reverse()` for "recent" views still works.
        return [Alerte(
            id=r.id, niveau=r.niveau, message=r.message,
            source_evenement=r.source_evenement,
            timestamp=r.timestamp, resolue=r.resolue,
        ) for r in rows]

    async def get_historique(self) -> list[HistoriqueEvenement]:
        from sqlalchemy import select
        from shared.database import AsyncSessionLocal
        from agents.orchestrateur.models import HistoriqueEvenementDB

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(HistoriqueEvenementDB))
            rows = result.scalars().all()
        return [HistoriqueEvenement(
            id=r.id, type_evenement=r.type_evenement,
            source_agent=r.source_agent, payload=r.payload or {},
            timestamp=r.timestamp, traite=r.traite,
            alertes_generees=r.alertes_generees or [],
        ) for r in rows]

    async def resoudre_alerte(self, alerte_id: str) -> bool:
        from shared.database import AsyncSessionLocal
        from agents.orchestrateur.models import AlerteDB

        async with AsyncSessionLocal() as db:
            alerte = await db.get(AlerteDB, alerte_id)
            if alerte is None:
                return False
            alerte.resolue = True
            await db.commit()
        return True

    async def get_stats(self) -> dict:
        historique = await self.get_historique()
        alertes_actives = await self.get_alertes(resolues=False)
        alertes_resolues = await self.get_alertes(resolues=True)
        return {
            "evenements_traites": len(historique),
            "alertes_actives": len(alertes_actives),
            "alertes_resolues": len(alertes_resolues),
            "regles_actives": len(self._regles),
        }


orchestrator_agent = OrchestratorAgent()
