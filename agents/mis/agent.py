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
        """MIS subscribes to project and resource events."""
        pass

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
