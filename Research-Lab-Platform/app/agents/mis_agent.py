# -*- coding: utf-8 -*-
from __future__ import annotations
from app.core.base_agent import BaseAgent
from app.core.event_bus import EventBus
from app.schemas.events import Event
from app.schemas.mis import Projet, Personnel, Equipement , Budget 


class MISAgent(BaseAgent):
    def __init__(self, name: str, event_bus: EventBus) -> None:
        super().__init__(name, event_bus)
        self._projets: dict[str, Projet] = {}
        self._personnels: dict[str, Personnel]={}
        self._equipements: dict[str, Equipement] = {}
        self._budgets: dict[str, Budget] = {}

    async def on_start(self) -> None:
        print(f"[{self.name}] Agent MIS demarre.")

    async def on_stop(self) -> None:
        print(f"[{self.name}] Agent MIS arrete.")

    async def handle_event(self, event: Event) -> None:
        print(f"[{self.name}] evenement recu : {event.type}")

    #Module Projets

    def create_projet(self, projet: Projet) -> Projet:
        self._projets[projet.id] = projet
        return projet

    def list_projets(self) -> list[Projet]:
        return list(self._projets.values())

    def get_projet(self, projet_id: str) -> Projet | None:
        return self._projets.get(projet_id)
    def update_projet(self, projet_id: str, data: dict) -> Projet | None:
        projet = self._projets.get(projet_id)
        if projet is None:
            return None
        updated = projet.model_copy(update=data)
        self._projets[projet_id] = updated
        return updated

    def delete_projet(self, projet_id: str) -> bool:
        if projet_id not in self._projets:
            return False
        del self._projets[projet_id]
        return True
    
    #Module Personnels
    def create_personnel(self,personnel:Personnel)-> Personnel:
        self._personnels[personnel.id]=personnel
        return personnel
    def list_personnel(self)->list[Personnel]:
        return list(self._personnels.values())
    def get_personnel(self, personnel_id: str) -> Personnel | None:
        return self._personnels.get(personnel_id)

    def update_personnel(self, personnel_id: str, data: dict) -> Personnel | None:
        personnel = self._personnels.get(personnel_id)
        if personnel is None:
            return None
        updated = personnel.model_copy(update=data)
        self._personnels[personnel_id] = updated
        return updated

    def delete_personnel(self, personnel_id: str) -> bool:
        if personnel_id not in self._personnels:
            return False
        del self._personnels[personnel_id]
        return True
    
    #Module Équipements

    def create_equipement(self, equipement: Equipement) -> Equipement:
        self._equipements[equipement.id] = equipement
        return equipement

    def list_equipements(self) -> list[Equipement]:
        return list(self._equipements.values())

    def get_equipement(self, equipement_id: str) -> Equipement | None:
        return self._equipements.get(equipement_id)

    def update_equipement(self, equipement_id: str, data: dict) -> Equipement | None:
        equipement = self._equipements.get(equipement_id)
        if equipement is None:
            return None
        updated = equipement.model_copy(update=data)
        self._equipements[equipement_id] = updated
        return updated

    def delete_equipement(self, equipement_id: str) -> bool:
        if equipement_id not in self._equipements:
            return False
        del self._equipements[equipement_id]
        return True
    
    #Module Budgets 

    def create_budget(self, budget: Budget) -> Budget:
        self._budgets[budget.id] = budget
        return budget

    def list_budgets(self) -> list[Budget]:
        return list(self._budgets.values())

    def get_budget(self, budget_id: str) -> Budget | None:
        return self._budgets.get(budget_id)

    def update_budget(self, budget_id: str, data: dict) -> Budget | None:
        budget = self._budgets.get(budget_id)
        if budget is None:
            return None
        updated = budget.model_copy(update=data)
        self._budgets[budget_id] = updated
        return updated

    def delete_budget(self, budget_id: str) -> bool:
        if budget_id not in self._budgets:
            return False
        del self._budgets[budget_id]
        return True
