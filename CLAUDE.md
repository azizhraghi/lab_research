> Current behavior and setup: see README.md and docs/IMPROVEMENTS-2026-09-08.md. The guidance below predates the latest integration and contains historical descriptions (including test-suite and environment-template claims). Do not use it as the current capability inventory.


# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An event-driven multi-agent platform for research-lab automation. A FastAPI gateway fronts 8 autonomous agents that communicate over a swappable event bus, backed by async SQLAlchemy (SQLite for dev, Postgres+pgvector for prod). A Vite/React/MUI SPA is the frontend.

The repo is a **merged monorepo** stitched from several contributors' projects (source comments reference "Friend 1" / "Friend 2"). The live app is the root-level `agents/` + `api/` + `shared/` + `frontend/`. The sibling top-level folders `AI Research Laboratory Platform/`, `research-lab-agents/`, and `Research-Lab-Platform/` are pre-merge sources — do not edit them expecting changes to reach the running app.

## Commands

Backend (run from repo root, with `.venv` activated):
- Run API: `python -m api.main` (uvicorn on :8000 with reload) or `uvicorn api.main:app --reload`
- Infra: `docker-compose up -d` (Postgres+pgvector, Redis; Kafka is behind the `kafka` compose profile)
- Migrations: `alembic upgrade head` / `alembic revision --autogenerate -m "msg"`
- Integration smoke test / seed data: `python test_agents.py` (injects an ArXiv source, runs the veille collection pipeline against real feeds + Mistral, adds a test researcher)
- Inspect dev DB: `python check_db.py`

Frontend (run from `frontend/`):
- Dev: `npm run dev` (Vite on :5173) — `build`: `npm run build`

Note: there is no formal pytest suite or lint config. `test_agents.py` is a live integration script, not unit tests.

## Configuration

`shared/config.py` is a pydantic-settings singleton loading `.env` then `.env.supabase.local`. Key flags:
- `DATABASE_URL` — defaults to `sqlite+aiosqlite:///./multiagent.db`; point at Postgres for pgvector features.
- `CREATE_SCHEMA_ON_STARTUP` — default `False`. When true, the API creates all tables on startup (dev only; prod uses Alembic).
- `EVENT_BUS_TYPE` — `redis` (default) | `kafka` | `memory`. Selects the bus implementation at import time.
- `DISABLE_AUTH` — dev-only bypass; `get_current_user` returns a stub user and skips Supabase validation. Pair with a blank `VITE_SUPABASE_*` on the frontend. Never enable in a deployed environment.
- `MISTRAL_API_KEY` — LLM calls (summarization, tagging, RAG) go through Mistral.

There is no backend `.env.example`; only `frontend/.env.example` (Vite public vars: `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY`, `VITE_API_BASE_URL`).

## Architecture

**Agents** (`agents/<name>/`): veille, bibliometrie, digitaltwin, mis, optimisation, simulation, orchestrateur, qualite. Each is a self-contained module: `agent.py`, `router.py`, `schemas.py`, and usually `models.py`, `tasks.py`, `services/`. Every agent subclasses `BaseAgent` (`shared/base_agent.py`) with a fixed lifecycle:
- `handle_event(event)` → optionally returns an `AgentAction`
- `propose_action(action)` → if `action_type` is in the agent's `requires_human_approval` list, emits `orch.action_proposed` to the orchestrator review queue; otherwise executes directly
- `execute_action(action)` → `ActionResult`

Agents are module-level singletons (e.g. `veille_agent`, `bibliometrie_agent`). Human-in-the-loop is a first-class concept: `ActionStatus.REQUIRES_APPROVAL` and per-agent approval gates (e.g. bibliometrie's `update_cv_profile`).

**Event bus** (`shared/event_bus.py`): `EventBusBase` with three interchangeable backends — Redis Streams (default), Kafka (aiokafka), InMemory (tests). A single `create_event_bus()` factory reads `EVENT_BUS_TYPE` and builds the module-level `event_bus` singleton used by all agents. Agents coordinate by publishing/subscribing typed `Event`s to named streams, not by calling each other. Redis publish failures degrade gracefully (logged, skipped).

**Event contract** (`shared/schemas.py`): `EventType` enum namespaces events per agent (`veille.*`, `bibliometrie.*`, ...). Core models: `Event`, `AgentAction`, `ActionResult`, `AuditEntry`, `ActionStatus`. This is the cross-agent contract — changing an event shape affects every subscriber.

**Gateway** (`api/main.py`): mounts each agent router under a prefix, all guarded by a global `Depends(get_current_user)`. Prefixes do NOT always match directory names — notably `/api/biblio` (bibliometrie) and `/api/twin` (digitaltwin); others match (`/api/veille`, `/api/simulation`, `/api/optimisation`, `/api/mis`, `/api/orchestrateur`, `/api/qualite`). CORS is locked to the Vite origin (:5173). All `models` modules are imported here so `Base.metadata` sees every table.

**Persistence**: async SQLAlchemy 2.0 via `shared/database.py` (`AsyncSessionLocal`, `get_db`, `Base`, `engine`). pgvector powers veille's dedup (vector similarity) and RAG — those features need Postgres, not the SQLite dev default.

**Frontend** (`frontend/src/`): Vite + React 18 + TypeScript, MUI 7 + Emotion + Tailwind, react-query, Supabase auth. Typed API clients in `src/api/`, auth in `src/auth/AuthContext.tsx`, shared client wiring in `src/lib/`.

## Agent-specific notes

- **veille** (literature monitoring): richest pipeline — `run_collection()` walks active `Source`s → fetch RSS/Atom (`fetch.py`, `fetchpubmed.py`) → embed → dedupe by vector similarity → create `Article`s → tag + summarize. Emits `article.discovered`.
- **bibliometrie** (researcher profiles/metrics): profiles persisted to `data/researchers.json`. Metrics use a 3-tier fallback: Google Scholar (`scholarly`, optionally via ScraperAPI) → Semantic Scholar → OpenAlex, degrading gracefully if `scholarly` can't import. Subscribes to `article.discovered` to append publications and regenerate CV PDFs (weasyprint/reportlab).

## Watch out for

- Several veille router endpoints carry "No auth required for dev testing" comments despite the global auth dependency — audit before deploying.
- pgvector-dependent behavior (veille dedup/RAG) silently differs on the SQLite dev DB.
