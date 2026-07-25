from __future__ import annotations
import re
from app.core.base_agent import BaseAgent
from app.core.event_bus import EventBus
from app.schemas.events import Event
from app.schemas.qualite import RapportQualite, NiveauQualite


class QualiteAgent(BaseAgent):
    def __init__(self, name: str, event_bus: EventBus) -> None:
        super().__init__(name, event_bus)
        self._rapports: list[RapportQualite] = []

    async def on_start(self) -> None:
        await self.event_bus.subscribe("qualite.validation_demandee", self.handle_event)
        print(f"[{self.name}] Agent Qualité démarré.")

    async def on_stop(self) -> None:
        print(f"[{self.name}] Agent Qualité arrêté.")

    async def handle_event(self, event: Event) -> None:
        print(f"[{self.name}] Événement reçu : {event.type}")
        entite_type = event.payload.get("entite_type")
        entite_id = event.payload.get("entite_id")
        data = event.payload.get("data", {})

        if entite_type == "projet":
            rapport = self.valider_projet(entite_id, data)
        elif entite_type == "personnel":
            rapport = self.valider_personnel(entite_id, data)
        elif entite_type == "equipement":
            rapport = self.valider_equipement(entite_id, data)
        elif entite_type == "budget":
            rapport = self.valider_budget(entite_id, data)
        else:
            return

        self._rapports.append(rapport)

        # Publie le résultat sur l'EventBus
        await self.event_bus.publish(Event(
            type="qualite.anomalie_detectee" if rapport.niveau == "non_conforme"
                 else "qualite.validation_ok",
            source_agent=self.name,
            payload={
                "entite_type": entite_type,
                "entite_id": entite_id,
                "niveau": rapport.niveau,
                "problemes": rapport.problemes,
                "conforme_rgpd": rapport.conforme_rgpd,
            }
        ))

   # VALIDATIONS MÉTIER

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
        return RapportQualite(
            entite_type="projet",
            entite_id=entite_id,
            niveau=niveau,
            problemes=problemes,
        )

    def valider_personnel(self, entite_id: str, data: dict) -> RapportQualite:
        problemes = []
        conforme_rgpd = True

        # Validation métier
        if not data.get("email"):
            problemes.append("Email manquant.")
            conforme_rgpd = False
        elif not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", data.get("email", "")):
            problemes.append("Format email invalide.")
            conforme_rgpd = False
        if not data.get("role"):
            problemes.append("Rôle non défini.")
        if not data.get("nom") or not data.get("prenom"):
            problemes.append("Nom ou prénom manquant.")
            conforme_rgpd = False

        # Vérification RGPD
        if not data.get("competences"):
            problemes.append("Aucune compétence renseignée.")

        niveau = self._calculer_niveau(problemes)
        return RapportQualite(
            entite_type="personnel",
            entite_id=entite_id,
            niveau=niveau,
            problemes=problemes,
            conforme_rgpd=conforme_rgpd,
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
        return RapportQualite(
            entite_type="equipement",
            entite_id=entite_id,
            niveau=niveau,
            problemes=problemes,
        )

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
        return RapportQualite(
            entite_type="budget",
            entite_id=entite_id,
            niveau=niveau,
            problemes=problemes,
        )

    # UTILITAIRES

    def _calculer_niveau(self, problemes: list[str]) -> NiveauQualite:
        if len(problemes) == 0:
            return "conforme"
        elif len(problemes) <= 2:
            return "avertissement"
        else:
            return "non_conforme"

    def get_rapports(self) -> list[RapportQualite]:
        return self._rapports

    def get_rapport_par_entite(self, entite_id: str) -> list[RapportQualite]:
        return
    def get_stats(self) -> dict:
        conformes = len([r for r in self._rapports if r.niveau == "conforme"])
        avertissements = len([r for r in self._rapports if r.niveau == "avertissement"])
        non_conformes = len([r for r in self._rapports if r.niveau == "non_conforme"])
        return {
            "total_rapports": len(self._rapports),
            "conformes": conformes,
            "avertissements": avertissements,
            "non_conformes": non_conformes,
        }