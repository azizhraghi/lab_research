# -*- coding: utf-8 -*-
"""MIS Agent – Management Information System for lab resources.

Adapted from Friend 1's MISAgent to use the monorepo's shared BaseAgent.
"""
from __future__ import annotations
from typing import Optional

from shared.base_agent import BaseAgent
from shared.schemas import Event, AgentAction, ActionResult


class MISAgent(BaseAgent):
    """Manages projects, personnel, equipment, and budgets."""

    name = "mis"
    permissions = ["mis.read", "mis.write"]
    requires_human_approval = ["mis.delete_projet"]

    async def _setup_subscriptions(self):
        """Request quality checks whenever a project's editable record changes."""
        await self._subscribe("events", self._on_bus_event)

    async def _on_bus_event(self, event: Event) -> None:
        if event.type not in {"projet.created", "projet.updated"}:
            return
        await self.emit_event("events", Event(
            id=f"mis-quality-{event.id}", type="qualite.validation_demandee",
            source_agent=self.name,
            payload={"entite_type": "projet", "entite_id": event.payload.get("id"),
                     "data": event.payload},
        ))

    async def handle_event(self, event: Event) -> Optional[AgentAction]:
        """Handle incoming events related to MIS resources."""
        print(f"[{self.name}] Event received: {event.type}")
        return None

    async def execute_action(self, action: AgentAction) -> ActionResult:
        return ActionResult(
            action_id=action.id,
            status="completed",
            result_data={"message": "Action executed by MISAgent"},
        )


mis_agent = MISAgent()
