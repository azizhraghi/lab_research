"""Transparent, deterministic planning for lab work.

This is intentionally a constraint heuristic, not a claim of optimal scheduling.
It proposes work against current MIS data and reports every unmet constraint for a
human reviewer to decide on.
"""
from __future__ import annotations

import json
from datetime import datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.mis.models import Equipement, Personnel
from agents.orchestrateur.models import PlanningTaskDB


_PRIORITY = {"critical": 0, "high": 1, "normal": 2, "low": 3}


def _words(values: list[str] | str | None) -> set[str]:
    if isinstance(values, str):
        try:
            values = json.loads(values)
        except json.JSONDecodeError:
            values = values.split(",")
    return {str(value).strip().casefold() for value in (values or []) if str(value).strip()}


def _window(task: PlanningTaskDB) -> tuple[datetime, datetime]:
    # Work backwards from a due date at 17:00, or schedule a one-day proposal
    # from now. Exact working-hours calendars belong in a later lab policy layer.
    end = datetime.combine(task.due_date, time(17, 0)) if task.due_date else datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(days=1)
    return end - timedelta(hours=task.duration_hours), end


def _overlaps(first: tuple[datetime, datetime], second: tuple[datetime, datetime]) -> bool:
    return first[0] < second[1] and second[0] < first[1]


async def create_plan(db: AsyncSession) -> tuple[list[dict], list[dict]]:
    """Return proposed assignments and explicit blockers for pending tasks."""
    tasks = (await db.execute(
        select(PlanningTaskDB).where(PlanningTaskDB.status == "pending")
    )).scalars().all()
    personnel = (await db.execute(select(Personnel))).scalars().all()
    equipment = {item.id: item for item in (await db.execute(select(Equipement))).scalars().all()}

    assignments: list[dict] = []
    conflicts: list[dict] = []
    reserved_people: dict[str, list[tuple[datetime, datetime]]] = {}
    reserved_equipment: dict[str, list[tuple[datetime, datetime]]] = {}

    # Previously approved work is a hard constraint for the next proposal.
    # Pending work is only reserved within this one draft, because it has not
    # yet been accepted by a human reviewer.
    committed = (await db.execute(
        select(PlanningTaskDB).where(PlanningTaskDB.status.in_(["planned", "in_progress"]))
    )).scalars().all()
    for task in committed:
        if task.scheduled_start is None or task.scheduled_end is None:
            continue
        committed_window = (task.scheduled_start, task.scheduled_end)
        if task.assigned_personnel_id:
            reserved_people.setdefault(task.assigned_personnel_id, []).append(committed_window)
        for equipment_id in task.required_equipment_ids or []:
            reserved_equipment.setdefault(equipment_id, []).append(committed_window)

    for task in sorted(tasks, key=lambda item: (_PRIORITY.get(item.priority, 2), item.due_date or datetime.max.date(), item.created_at)):
        window = _window(task)
        required_skills = _words(task.required_skills)
        eligible_people = [
            person for person in personnel
            if person.disponible
            and (not person.projet_actuel_id or person.projet_actuel_id == task.project_id)
            and required_skills.issubset(_words(person.competences))
            and not any(_overlaps(window, busy) for busy in reserved_people.get(person.id, []))
        ]
        unavailable_equipment = [
            equipment_id for equipment_id in task.required_equipment_ids
            if equipment_id not in equipment or equipment[equipment_id].etat != "operationnel"
        ]
        busy_equipment = [
            equipment_id for equipment_id in task.required_equipment_ids
            if equipment_id in equipment and any(_overlaps(window, busy) for busy in reserved_equipment.get(equipment_id, []))
        ]
        reasons: list[str] = []
        if not eligible_people:
            skill_text = ", ".join(sorted(required_skills)) or "available staff"
            reasons.append(f"No available person matches: {skill_text}.")
        if unavailable_equipment:
            reasons.append(f"Equipment unavailable or not operational: {', '.join(unavailable_equipment)}.")
        if busy_equipment:
            reasons.append(f"Equipment already reserved in this proposed schedule: {', '.join(busy_equipment)}.")
        if reasons:
            conflicts.append({"task_id": task.id, "title": task.title, "reasons": reasons})
            continue

        # Prefer staff already attached to the project, then alphabetically so
        # identical inputs always produce the same reviewable proposal.
        chosen = sorted(
            eligible_people,
            key=lambda person: (person.projet_actuel_id != task.project_id, person.nom.casefold(), person.prenom.casefold()),
        )[0]
        reserved_people.setdefault(chosen.id, []).append(window)
        for equipment_id in task.required_equipment_ids:
            reserved_equipment.setdefault(equipment_id, []).append(window)
        assignments.append({
            "task_id": task.id,
            "title": task.title,
            "personnel_id": chosen.id,
            "personnel_name": f"{chosen.prenom} {chosen.nom}",
            "equipment_ids": task.required_equipment_ids,
            "scheduled_start": window[0].isoformat(),
            "scheduled_end": window[1].isoformat(),
            "rationale": "Matches required skills, availability and the proposed resource window.",
        })
    return assignments, conflicts
