from __future__ import annotations
from datetime import datetime
from app.core.base_agent import BaseAgent
from app.core.event_bus import EventBus
from app.schemas.events import Event
from app.schemas.orchestrateur import Alerte, HistoriqueEvenement

class OrchestratorAgent(BaseAgent):
    def __init__(self, name: str, event_bus: EventBus) -> None:
        super().__init__(name, event_bus)
        self._alertes: list[Alerte] = []
        self._historique: list[HistoriqueEvenement] = []

        # Table de routage : type d'événement → liste de handlers
        self._regles: dict[str, list] = {
            # MIS
            "projet.created":               [self._verifier_projet],
            "projet.statut_change":         [self._verifier_statut_projet],
            "budget.depense":               [self._verifier_seuil_budget],
            "equipement.etat_change":       [self._verifier_equipement],
            "personnel.indisponible":       [self._verifier_personnel],
            # Veille Scientifique
            "veille.article_trouve":        [self._notifier_chercheurs],
            "veille.resume_genere":         [self._declencher_validation_qualite],
            # Bibliométrie
            "bibliometrie.profil_mis_a_jour": [self._synchroniser_mis],
            "bibliometrie.cv_genere":       [self._archiver_document],
            # Simulation
            "simulation.terminee":          [self._declencher_optimisation],
            "simulation.calibration_ok":    [self._archiver_resultats],
            # Optimisation
            "optimisation.strategie_calculee": [self._notifier_strategie],
            "optimisation.contrainte_violee":  [self._alerte_contrainte],
            # Qualité
            "qualite.anomalie_detectee":    [self._suspendre_projet],
            "qualite.validation_ok":        [self._marquer_conforme],
        }

    async def on_start(self) -> None:
        # Souscription à tous les types d'événements connus
        for type_evenement in self._regles:
            await self.event_bus.subscribe(type_evenement, self.handle_event)
        print(f"[{self.name}] Orchestrateur démarré — {len(self._regles)} règles actives.")

    async def on_stop(self) -> None:
        print(f"[{self.name}] Orchestrateur arrêté.")

    async def handle_event(self, event: Event) -> None:
        print(f"[{self.name}] Événement reçu : {event.type} de {event.source_agent}")

        alertes_ids = []

        # Appel de tous les handlers associés à ce type d'événement
        handlers = self._regles.get(event.type, [])
        for handler in handlers:
            alerte = await handler(event)
            if alerte:
                self._alertes.append(alerte)
                alertes_ids.append(alerte.id)

        # Log dans l'historique
        self._historique.append(HistoriqueEvenement(
            type_evenement=event.type,
            source_agent=event.source_agent,
            payload=event.payload,
            alertes_generees=alertes_ids,
        ))

    # ─────────────────────────────────────────
    # RÈGLES MIS
    # ─────────────────────────────────────────

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
        if event.payload.get("etat") == "en_maintenance":
            return Alerte(
                niveau="info",
                message=f"Équipement '{event.payload.get('nom', '?')}' en maintenance.",
                source_evenement=event.type,
            )
        if event.payload.get("etat") == "indisponible":
            return Alerte(
                niveau="orange",
                message=f"Équipement '{event.payload.get('nom', '?')}' indisponible.",
                source_evenement=event.type,
            )
        return None

    async def _verifier_personnel(self, event: Event) -> Alerte | None:
        return Alerte(
            niveau="info",
            message=f"Personnel '{event.payload.get('nom', '?')}' indisponible — vérifier projets impactés.",
            source_evenement=event.type,
        )

    # ─────────────────────────────────────────
    # RÈGLES VEILLE SCIENTIFIQUE
    # ─────────────────────────────────────────

    async def _notifier_chercheurs(self, event: Event) -> Alerte | None:
        print(f"[{self.name}] Nouvel article : {event.payload.get('titre', '?')} — chercheurs notifiés.")
        return None

    async def _declencher_validation_qualite(self, event: Event) -> Alerte | None:
        print(f"[{self.name}] Résumé généré → déclenchement validation Qualité.")
        return None

    # ─────────────────────────────────────────
    # RÈGLES BIBLIOMÉTRIE
    # ─────────────────────────────────────────

    async def _synchroniser_mis(self, event: Event) -> Alerte | None:
        print(f"[{self.name}] Profil mis à jour → synchronisation MIS.")
        return None

    async def _archiver_document(self, event: Event) -> Alerte | None:
        print(f"[{self.name}] CV généré → archivage MIS.")
        return None

    # ─────────────────────────────────────────
    # RÈGLES SIMULATION
    # ─────────────────────────────────────────

    async def _declencher_optimisation(self, event: Event) -> Alerte | None:
        print(f"[{self.name}] Simulation terminée → déclenchement Optimisation automatique.")
        return None

    async def _archiver_resultats(self, event: Event) -> Alerte | None:
        print(f"[{self.name}] Calibration OK → archivage résultats dans MIS.")
        return None

    # ─────────────────────────────────────────
    # RÈGLES OPTIMISATION
    # ─────────────────────────────────────────

    async def _notifier_strategie(self, event: Event) -> Alerte | None:
        print(f"[{self.name}] Stratégie calculée : {event.payload.get('strategie', '?')} — notification équipe.")
        return None

    async def _alerte_contrainte(self, event: Event) -> Alerte | None:
        return Alerte(
            niveau="critique",
            message=f"Contrainte violée en optimisation : {event.payload.get('contrainte', '?')}.",
            source_evenement=event.type,
        )

    # ─────────────────────────────────────────
    # RÈGLES QUALITÉ
    # ─────────────────────────────────────────

    async def _suspendre_projet(self, event: Event) -> Alerte | None:
        return Alerte(
            niveau="critique",
            message=f"Anomalie détectée par Qualité — projet {event.payload.get('projet_id', '?')} suspendu.",
            source_evenement=event.type,
        )

    async def _marquer_conforme(self, event: Event) -> Alerte | None:
        print(f"[{self.name}] Validation Qualité OK → données marquées conformes RGPD.")
        return None

    # ─────────────────────────────────────────
    # ACCESSEURS (pour les endpoints)
    # ─────────────────────────────────────────

    def get_alertes(self, resolues: bool = False) -> list[Alerte]:
        return [a for a in self._alertes if a.resolue == resolues]

    def get_historique(self) -> list[HistoriqueEvenement]:
        return self._historique

    def resoudre_alerte(self, alerte_id: str) -> bool:
        for alerte in self._alertes:
            if alerte.id == alerte_id:
                alerte.resolue = True
                return True
        return False

    def get_stats(self) -> dict:
        return {
            "evenements_traites": len(self._historique),
            "alertes_actives": len(self.get_alertes(resolues=False)),
            "alertes_resolues": len(self.get_alertes(resolues=True)),
            "regles_actives": len(self._regles),
        }