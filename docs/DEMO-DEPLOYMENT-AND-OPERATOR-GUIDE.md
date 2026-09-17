> Updated behavior (8 September 2026): see the root README and IMPROVEMENTS-2026-09-08.md. Project editing and direct resource setup are available; operational calculations require current reviewed field data; unknown user roles now receive read-only access. Calibration reports in-sample Fit RMSE, not independent validation.

# LRSTE Platform: Demo, Deployment and Operator Guide

## What the platform is

LRSTE is an internal laboratory workbench for:

- scientific watch and bibliometric follow-up;
- research-project, equipment and budget operations;
- reviewed field measurements and irrigation decision support; and
- a deliberately curated public catalogue of approved research content.

It is designed to help researchers, technicians, reviewers, administrators and the laboratory director work from a common, traceable workspace. It does **not** autonomously control irrigation hardware or replace an agronomist's judgement.

The agent architecture should be described precisely: **six event-driven agents** (Scientific Watch, Bibliometrics, Digital Twin/IoT, MIS, Quality and Orchestrator) share events and alerts. **Simulation** and **Optimisation** are genuine scientific analysis modules, started by a researcher for a selected parcel; they are not autonomous background agents.

## Important scientific and operational limits

- The Digital Twin uses a parcel-level FAO-56 soil-water-balance approach. It is not SWAT, EPANET, HEC-HMS, WEAP or MODFLOW.
- Optimisation produces a transparent threshold-and-water-quota schedule. It is not a validated Bayesian or genetic optimiser.
- A recommendation is decision support only. A reviewer must approve it and an operator must record what was actually applied.
- Calibration requires real, reviewed readings. Demonstration, test and simulated readings are excluded.
- A public item appears only after an authorised reviewer has approved a redacted public record; internal budgets, staff, risks and raw field measurements are never exposed by the public API.

## Who uses what

| Role | Main work |
| --- | --- |
| Field technician or gateway | Registers a gateway, submits readings, corrects information, confirms irrigation actually applied. |
| Researcher | Reviews measurements, runs scenarios and schedules, manages watch topics and project work. |
| Reviewer / scientific lead | Accepts or rejects anomalies and recommendations; approves public content. |
| Administrator | Manages staff, equipment, budgets, roles, production health and failed event deliveries. |
| Laboratory director | Reviews project reports, risks, workload, alerts and curated public outputs. |
| Public visitor | Reads only approved publications, researcher profiles, project summaries and dataset catalogue entries. |

## Live demonstration setup

This platform should be demonstrated as a live walkthrough of its real screens and workflows. Do **not** seed synthetic records or present invented measurements as laboratory evidence.

Before recording, point the backend at the database you actually intend to demonstrate, apply migrations, sign in with the intended account, and verify both endpoints:

```powershell
\.venv\Scripts\python.exe -m alembic upgrade head
\.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

In a second PowerShell window:

```powershell
$env:VITE_API_BASE_URL = "http://127.0.0.1:8000"
npm --prefix frontend run dev -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173`. The backend CORS origin must exactly match the frontend address and port. Use `DISABLE_AUTH=true` only if you are deliberately running a local development environment; it must never be used in staging or production.

## Recommended supervisor demonstration (7–10 minutes)

1. Open the **Public Visitor Portal** first. Explain that it exposes only approved, redacted catalogue content; empty lists are correct until something has been reviewed and published.
2. Select **Lab sign in**, then open **Research Projects**. Walk through creating or managing a project, then point out the available milestones, deliverables, budget lines, risks, reservations, maintenance reminders, workload and reports.
3. Open **IoT Monitoring**. Explain the live operational route: measurement → quality check → reviewer → recommendation → approval → actual irrigation log. Do not imply that a recommendation has been field-validated before real readings exist.
4. Open **Digital Twins**. Show how a researcher can configure a scenario or water-constrained schedule. Say that the module compares assumptions and proposed schedules; it does not operate pumps and must be reviewed.
5. Open **Scientific Watch** and **Researchers**. Show source management, themes/digest/review workflow and researcher features. Do not trigger external collection during a presentation unless credentials and network access have already been tested.
6. Open **AI Agents**. State the six-event-agent/two-on-demand-module distinction. Show event history, alerts and planning tasks, not a claim of autonomous scientific decision making.

## Module guide

### Dashboard

The Dashboard is the landing page and high-level status view. It gives quick counts for projects, publications, parcels and module availability. When real setup steps are still missing, it shows a first-use checklist linking to Projects, Researchers, Scientific Watch and IoT Monitoring. It also contains the **Laboratory activity timeline**, which combines persisted agent events, collection runs, field tasks, measurement reviews, planning tasks and active alerts. Filter it by workflow and select an item to open the owning module. Treat counts as navigation cues; use the source module for operational detail.

### AI Research Assistant

The floating assistant is a grounded workspace guide. It searches only the collected publications and researcher profiles returned by the platform, and can answer `Platform status`, `What should I do next?`, or `What can you help me with?` from current project, source, parcel, alert and measurement-review counts. Its action links open the relevant module.

It is intentionally not a general scientific chatbot: it does not invent literature, sensor readings, research conclusions or irrigation instructions. If the workspace is empty, it explains the missing setup step rather than fabricating an answer.

### Research Projects (MIS)

This is the lab operations workspace. It manages projects, personnel, equipment and budgets, then adds the practical controls laboratories usually keep in spreadsheets or email:

- milestones and deliverables with owners and due dates;
- risks and mitigations;
- budget lines, commitments and expenses;
- equipment reservations plus maintenance and calibration reminders;
- staff workload; and
- project reports, deadlines and budget alerts.

Use it when creating a real project, allocating a person or instrument, or preparing a monthly progress review. The Quality and Orchestrator agents receive relevant changes and can raise visible alerts. Do not publish a project from its internal record: create and approve a deliberately redacted public summary.

### Publications and Researchers (Bibliometrics)

The Publications area stores research outputs and provides search, filtering and article-level review. The Researchers area holds the authoritative database-backed researcher record, indicators, linked publications and CV generation.

Researcher metric synchronisation can use external sources such as ORCID, Semantic Scholar, OpenAlex, Google Scholar and Scopus when the required identifiers, credentials and network access are available. Verify imported identities and citations before using them in a report. The legacy JSON profile endpoints are not an operational source of truth and should not be used for new data.

### Scientific Watch

Scientific Watch collects configured RSS/Atom and supported scientific sources, de-duplicates articles, adds tags and summaries, then gives researchers a review inbox. Researchers can maintain themes and keywords, save/read/share items and receive scheduled digests. The automatic collection scheduler is intended to run once per day in one selected application process.

Before enabling a real source, test it with its exact URL and verify the stored DOI, authors, title and date. A failed external source must remain visible as failed; do not silently treat an empty collection as a successful run.

### Digital Twins, Simulation and Optimisation

Create a parcel with crop, area, soil-water parameters and coordinates. The Digital Twin combines accepted readings with a weather forecast to calculate a transparent water balance and recommendation.

- **Simulation** compares a baseline with a researcher-chosen scenario (for example higher evapotranspiration or lower rainfall).
- **Optimisation** proposes a schedule under daily and total water constraints.
- **Recommendation review** keeps generated advice separate from approval and from the actual irrigation record.

Use parcel coordinates only to obtain local weather support today. The GIS Maps workspace is still planned and does not provide a complete map layer or spatial analysis service.

### IoT Monitoring and field workflow

IoT Monitoring is the operational field-data screen. Readings may arrive through authenticated gateways, manual entry or controlled CSV import. The system records sensor health, last contact and failed-upload information, flags suspicious readings, supports annotation/correction/acceptance/rejection, and shows a review queue.

The required real-world workflow is:

1. Register each gateway and retain its token securely.
2. Ingest or import a measurement with source, timestamp and units.
3. Review anomalies; correct, annotate, accept or reject them.
4. Generate a recommendation from accepted data and forecast assumptions.
5. Have a responsible researcher approve or reject it.
6. Convert an approved schedule to a field task where appropriate.
7. Record the irrigation that was actually applied, including amount, method and operator.
8. After enough real, reviewed measurements exist, evaluate calibration and validation against outcomes.

Never use test/demo readings to justify an operational schedule or calibration result.

### Quality, Orchestrator and AI Agents

The Quality Agent checks relevant project, budget, personnel and equipment records for completeness and rule violations. The Orchestrator routes events, persists alerts/history and supports planning tasks such as staff/equipment/deadline conflict checks.

The **AI Agents** screen is an operations console, not proof that every module continuously works autonomously. It shows persisted routed events, active alerts and on-demand modules. For production, administrators should inspect `/ready` and the outbox operation endpoint, then resolve the dependency or retry failed delivery when needed.

### Administration

Use Administration for controlled operational actions and public-content governance. Only authorised users should manage roles, review public catalogue entries or access operational error information. Keep public consent evidence and the approval identity/date for researcher profiles.

### Public Visitor Portal

The visitor portal uses separate anonymous, read-only endpoints. It can show only published researcher profiles with consent, approved publication records, redacted project summaries and published dataset catalogue metadata. It must never query internal MIS, raw sensor or budget endpoints.

### Institutional content and planned navigation

**Theses**, **Events** and **News** now support administrator-controlled drafting, publishing and withdrawal. Public visitors see published records only. Event registration and thesis-progress supervision are not implemented; see `INSTITUTIONAL-PUBLISHING-2026-09-11.md`.

**GIS Maps** remains planned. **Open Data Catalogue** public display is implemented, but a dedicated internal staff curation screen remains future UI work.

### Project research dossier

In Research Projects, select the project under Laboratory operations and scroll to Project research dossier. Save research questions, approach, findings and missing evidence. To add literature, first include a paper in your private Scientific Watch review, then select it in the dossier and explain its project relevance. Adding a paper shares its source snapshot and the new project rationale with internal project users; private screening notes are not copied.

Export readable dossier downloads a standalone HTML working report containing the saved narrative, selected literature, current milestones, deliverables, risks and outstanding-work warnings. Save edits before exporting. This report is not a signed supervisor approval, immutable archive or scientific validation. See `PROJECT-DOSSIER-2026-09-16.md` for verification and access limits. Apply `alembic upgrade head` before starting this revision.

## Production deployment checklist

Before any lab rollout, use a non-demo environment and verify every item below:

- PostgreSQL with the required extensions/migrations, not SQLite;
- Redis or Kafka event bus, not in-memory event delivery;
- Supabase URL and publishable key configured; `DISABLE_AUTH=false`;
- a private `GATEWAY_TOKEN_PEPPER`, stored as a secret;
- exact `CORS_ALLOWED_ORIGINS` for the hosted frontend—never `*`;
- Alembic migrations applied before starting the API; `CREATE_SCHEMA_ON_STARTUP=false`;
- one designated Scientific Watch scheduler process, or an external scheduled trigger;
- Mistral credentials and quotas tested if AI summaries/embeddings are enabled;
- database backup, log collection and an identified operator for failed outbox events;
- `GET /health` returns `ok`, and authenticated operational checks show `GET /ready` as `ready` after deployment.

The included Compose file provisions dependencies but is not yet a full hardened application-container deployment. Until an application image, reverse proxy/TLS, secrets management, backup job and repeatable CI smoke test are supplied, deploy with a controlled process manager or hosting platform and document its exact run command.

## Presentation wording that is accurate

Use: “The platform gives the lab a reviewed operational chain from measurement to proposed irrigation action, plus research monitoring and project management.”

Avoid: “The AI autonomously irrigates fields,” “the Digital Twin is a complete hydrological simulator,” “the optimiser is scientifically validated,” or “all eight agents run autonomously.”

## Quick troubleshooting

| Symptom | First check |
| --- | --- |
| Browser says network/CORS error | The frontend URL exactly matches `CORS_ALLOWED_ORIGINS`; API is available at `/health`. |
| API returns 401/503 in local demo | Frontend/back-end auth modes disagree. Use the isolated demo commands above only. |
| Empty screen after demo seed | Confirm the frontend uses the same API URL and the backend uses the intended `DATABASE_URL`. |
| `/ready` fails | Check database, selected event bus, agent startup logs and `/operations/outbox`. |
| No recommendation | Confirm a parcel, accepted readings, weather data and required input units. |
| Calibration unavailable | This is correct until enough real, reviewed `field` or `field_import` readings exist. |
| Watch collection is empty | Verify source URL, source state, network access and credentials; inspect the source error rather than inventing a successful result. |


## Research release update (17 September 2026)

Research Projects now supports evidence-linked findings, paired baseline evaluations and preserved supervisor submissions. Reviewers can request changes or approve another user's submission; later working edits never alter that snapshot. Dashboard exposes pending reviews, overdue deliverables, open risks and administrator delivery/consumer outcomes. Researchers includes manual identifier review history and metric provenance. See SUPERVISOR-HANDOVER-2026-09-16.md for the complete demonstration.

The original docker-compose.yml remains a dependency-only setup. The new compose.demo.yml packages the complete application for localhost demonstration; it bypasses auth and must not be exposed as production. Docker is unavailable on the verification machine, so package startup and real PostgreSQL/Redis recovery remain unverified. See RESEARCH-RELEASE-OPERATIONS.md for commands and CI checks.
