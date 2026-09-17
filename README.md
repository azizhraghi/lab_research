# LRSTE laboratory workbench

An internship prototype integrating scientific watch, researcher profiles, laboratory project operations and reviewed parcel-irrigation decision support.

The live application is `api/` + `agents/` + `shared/` + `frontend/`. Top-level HTML/JS files and the pre-merge sibling folders are historical prototypes, not the running application.

## Current scope

- Public catalogue of reviewed researcher profiles, publications, project summaries and dataset metadata.
- Administrator draft, edit, publish and withdraw workflows for news, events and thesis records, with public display of published content only.
- Project creation and editing, all four lifecycle states, milestones, deliverables, risks, budget entries and equipment operations.
- Scientific-source collection, embedding/deduplication, tags and summaries, with persisted failure reporting.
- Field measurement ingestion, quality review, parcel-water recommendations, reviewer approval and recorded application.
- On-demand water-balance scenarios, quota-constrained schedules and calibration candidates.
- Six coordinated workflow modules (watch, bibliography, MIS, quality, twin and orchestrator); simulation and optimization are on-demand calculations. MIS requests project-quality checks when projects are created or edited.

This is a parcel-level simplified water-balance prototype, not a validated hydrological model or autonomous irrigation controller. GIS layers, event registration and internal thesis-progress tracking remain planned. Real laboratory data is still to be obtained for evaluation.

## Local setup (PowerShell, fresh checkout)

The current local verification used Python 3.14.6 and Node 24.18.0. Dependencies are in `requirements/locked.txt` and `frontend/package-lock.json`.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements/locked.txt
npm --prefix frontend ci
Copy-Item .env.example .env
Copy-Item frontend/.env.example frontend/.env
```

For an existing checkout, edit the existing environment files instead of overwriting them. `.env.supabase.local`, if present, is loaded after `.env`; process environment variables override both.

For a local-only development run, use a dedicated database and keep the collection scheduler off until sources and credentials are ready:

```powershell
$env:DATABASE_URL='sqlite+aiosqlite:///./local-development.db'
$env:ENVIRONMENT='development'
$env:EVENT_BUS_TYPE='memory'
$env:DISABLE_AUTH='true'
$env:CREATE_SCHEMA_ON_STARTUP='false'
$env:VEILLE_SCHEDULER_ENABLED='false'
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

In a second PowerShell window, leave the two Supabase values empty in `frontend/.env` for this local-only auth bypass. Do not use that configuration for a hosted application.

```powershell
$env:VITE_API_BASE_URL='http://127.0.0.1:8000'
npm --prefix frontend run dev -- --host 127.0.0.1 --port 5173
```

Open [the local application](http://127.0.0.1:5173) and [API documentation](http://127.0.0.1:8000/docs). `/health` checks process health; `/ready` checks the configured database, bus, agent state and outbox failures. These checks do not establish scientific validity or verify every external provider.

For real authentication, configure matching frontend/backend Supabase public settings, set `DISABLE_AUTH=false`, and assign `app_metadata.lab_role` through a trusted administrator. Supported roles are `viewer`, `researcher`, `reviewer`, `administrator`. Missing or unknown roles now default to **read-only viewer**. Existing users who previously relied on an implicit researcher role need an explicit role assignment. Never let user-editable metadata determine authorization.

## Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

The backend regression suite applies migrations to a temporary SQLite database and uses synthetic fixtures and mocked external responses. It never reads or writes the laboratory database and requires no live API credentials. It checks valid workflow outcomes as well as rejection paths. The suite uses the Python standard library's `unittest`; no additional test framework is required.

The repository CI definition runs these checks when pushed. Local success does not imply that a remote CI run or clean dependency installation has already been verified.

## Water workflow rules

All new measurements start pending validation; client-supplied quality flags cannot approve them. Each imported CSV row receives its own quality check. Processed measurements cannot be overwritten through CSV; use the review workflow or add a new observation to preserve provenance.

Operational advice, scenarios and schedules require the **newest** measurement to be accepted field data (`field`, `field_import` or `gateway`). The system does not silently fall back to an older good reading when the newest is rejected or pending. Demo/test/unknown origins, future timestamps beyond five minutes and stale readings are blocked. The freshness limit is `SENSOR_STALE_AFTER_HOURS` (48 by default); agree a suitable field sampling protocol with the supervisor.

Approval rechecks the source measurement. Legacy schedules without a source-reading reference must be regenerated. Erroneous measurements require correction or rejection; a correction containing a physical error is rejected. An already traced measurement cannot be rewritten through a correction that would change recorded advice.

Calibration uses reviewed field history, including gateways. **Fit RMSE** measures fit to the calibration data; it is not independent validation. Obtain separate evaluation data before making accuracy or water-saving claims.

## Handover documents

- `docs/DEMO-DEPLOYMENT-AND-OPERATOR-GUIDE.md`: screen guide and deployment prerequisites.
- `docs/IMPROVEMENTS-2026-09-08.md`: fixes, validation and remaining work from the submission audit.
- `docs/FIELD-EVALUATION-PROTOCOL.md`: data request and evaluation checklist for the supervisor.
- `docs/INTERNSHIP-SUBMISSION-ASSESSMENT-2026-09-07.md`: historical baseline audit; its defects are not all current.

The original cahier remains the scope reference. `HANDOFF.md`, `CLAUDE.md` and the older capacities document contain historical claims; use this README and the dated improvement record for current behavior. Before sending the repository, include all intended application files and migrations in the submission revision. Do not include `.env` files, local databases, logs or pre-merge reference copies. There is no claim of production readiness until PostgreSQL/broker deployment, authentication, backups and external integrations have been verified.

Institutional publishing: see `docs/INSTITUTIONAL-PUBLISHING-2026-09-11.md` for scope and verification. Run `alembic upgrade head` before starting this revision; it adds the institutional content table.

Project completion controls and a project-wide JSON report are now available in Research Projects. See `docs/PROJECT-WORKFLOW-2026-09-12.md` for the tested walkthrough and remaining limits.

Public-source integration evidence and the opt-in ORCID/CV check are documented in `docs/PUBLIC-INTEGRATIONS-2026-09-12.md`. ORCID import and PubMed metadata retrieval have live examples; citation metrics and complete live LLM enrichment remain unverified.

Scientific Watch now includes private topic reviews with live PubMed abstracts, saved screening decisions and annotated bibliography export. See docs/LITERATURE-REVIEW-2026-09-12.md for the walkthrough, evidence and limits. Apply alembic upgrade head before starting this revision.

Project research dossiers connect questions, methods, findings and limitations with selected literature and project progress. Working HTML reports and preserved supervisor submissions are available. See docs/SUPERVISOR-HANDOVER-2026-09-16.md; docs/PROJECT-DOSSIER-2026-09-16.md describes the historical first milestone. Run alembic upgrade head.


Research release (verified 17 September): evidence-linked findings, paired baseline evaluations, preserved supervisor submissions and decisions, attention dashboard, bibliographic identity-review history and metric provenance are implemented. See docs/SUPERVISOR-HANDOVER-2026-09-16.md and docs/RESEARCH-RELEASE-OPERATIONS.md. These supersede earlier statements that dossier review/version snapshots are future work. Run alembic upgrade head. 30 offline tests pass; the full localhost Compose demo and recovery CI are supplied but Docker execution remains unverified on this machine.

Six workflow improvements (17 September): guided project setup and budget history, direct literature-to-project sharing, publication metadata checks, parcel evidence trail, submission comparison and deployment preflight. See docs/WORKFLOW-UPGRADES-2026-09-17.md for behavior and verification limits.
