> Historical baseline audit. See IMPROVEMENTS-2026-09-08.md for implemented fixes, verification and remaining gaps.

# Internship submission assessment

Reviewed 7 September 2026. Assessment of the current local working tree, not just committed HEAD.

## Verdict

**A substantial internship prototype with a credible purpose; not ready to hand over unchanged as a finished operational laboratory platform.**

The strongest contribution is an integrated workbench connecting laboratory projects, research monitoring and a traceable parcel-water decision workflow. There is real persistence, domain logic, event handling, human approval and UI integration. This is meaningful engineering work.

Whether it meets the internship contract depends on the agreed scope. The repository's cahier des charges describes a much larger platform: a full laboratory website, several hydrological domains, extensive integrations, data infrastructure and industrial deployment. The current project delivers a subset. No supervisor-confirmed reduced scope was available during this audit. Therefore this report does not assign a completion percentage or predict an academic grade.

| Intended submission | Assessment |
| --- | --- |
| Progress demonstration for feedback | Suitable now if defects and demo data are disclosed |
| Final internship MVP | Plausible after targeted fixes, evidence and a reproducible handover |
| Complete implementation of the original cahier | No |
| Daily operational or scientifically validated irrigation system | Not established |

## What was actually verified

- Frontend TypeScript check passed; Vite production build passed. Build output was approximately 1.09 MB JavaScript, 289 kB compressed, in one main bundle. The initial sandbox prevented the build subprocess; the authorized normal build succeeded.
- All Alembic migrations applied to a new, isolated SQLite database through `n4c1d8e2f7a9`.
- FastAPI startup and readiness succeeded with SQLite, an in-memory bus and the watch scheduler disabled.
- The current OpenAPI schema exposes **133 operations**. All **35 GET paths without path parameters** returned 200 under the audit administrator identity. These are smoke checks, not proof that all 133 operations work.
- Project creation, parcel creation and measurement ingestion succeeded.
- A 60 mm test reading generated a persisted 42 mm irrigation recommendation through the background quality/twin chain.
- Logging application of an unapproved recommendation returned 409. A researcher identity could not approve it (403); administrator approval and subsequent application logging succeeded.
- An erroneous 999 mm reading received `quality_flag=error`, `review_status=pending`.
- With auth enabled and no bearer token, a public catalogue GET returned 200, while internal projects and public administration returned 401. Actual Supabase sign-in was not exercised.
- An unpublished internal project did not appear in the public catalogue.
- Browser inspection covered welcome, public portal, home, dashboard and research-project screens, using the isolated audit database. The dashboard rendered coherently and showed real persisted activity.

Evidence is in `docs/audit-2026-09-07-evidence.json`; the reproducer is `scripts/audit_submission.py`. Test records are explicitly synthetic and stored only in `audit-2026-09-07.db`. The script is a diagnostic reproducer, not an assertion-based regression suite. Repeated runs append isolated test records. Original laboratory databases were opened read-only for aggregate counts.

Not verified: live scholarly/LLM/weather integrations, actual sensor hardware, authenticated multi-user browser workflows, PostgreSQL/pgvector, Redis/Kafka recovery, deployment, performance under load, accessibility/mobile coverage, and every CRUD or public publishing operation. The external failure test below used a mocked network failure, not a live service request.

## Does the project solve the intended problem?

| Requirement area | Current contribution | Remaining gap |
| --- | --- | --- |
| Public laboratory presence | Separate reviewed public catalogue with researcher consent and redacted project records | A catalogue is not the complete institutional website; theses, events, news and GIS remain placeholders; other original sections need an agreed disposition |
| Internal laboratory operations | Projects, personnel, equipment, budgets, milestones, deliverables, risks, reservations and reports have backend implementations and supporting screens | Core project lifecycle is incomplete in the UI; staff/equipment/budget setup is buried in Administration; some update operations fail |
| Scientific watch | Source collection, embedding/deduplication, tagging, summaries, inbox and digest code | Live integration evidence absent in this audit; failure reporting is incorrect in a reproduced case |
| Bibliometrics | Researcher records, identifier-based synchronization, publications and CV code | Live identity matching, metric accuracy and PDF delivery need a documented real example |
| Parcel digital twin | Simplified water balance, quality review, recommendations, approval and application log | Manual advice bypasses quality gating; no local real-field validation evidence |
| Simulation and optimization | Actual scenario projection and constrained threshold/greedy schedule calculations | No proof of scientific predictive accuracy or optimality; not SWAT/EPANET or multi-domain modeling |
| Agent coordination | Real event-driven chains, outbox and receipts, persisted alerts/history | Agent count overstates autonomous behavior; delivery recovery not operationally validated here |
| Handover and deployment | Environment examples, migrations, locked requirements and operator guide | Dirty source tree, inconsistent documentation, no discovered maintained CI/regression suite or complete application deployment package |

The internship story should be: **“I implemented and evaluated an integrated prototype for laboratory operations and reviewed parcel-irrigation decision support.”** It should explain what was selected from the brief, why those choices serve the laboratory, and what evidence supports each outcome.

## Issues to address before final submission

### 1. The advertised quality gate can be bypassed — high priority, reproduced

After quality processing classified the 999 mm measurement as erroneous and pending review, `POST /api/twin/parcels/{id}/recommend` returned 200 and advised zero irrigation from that same measurement, with a 0.90 reserve score.

`agents/digitaltwin/agent.py:105` selects a source reading without checking quality, review status, provenance or freshness before calculation. The manual router delegates directly to it. Simulation and optimization also load readings without quality filtering (`agents/simulation/agent.py:53`, `agents/optimisation/agent.py:53`), although their resulting bad-data behavior was not separately executed.

This breaks the central promise that reviewed measurements underpin advice. Apply one shared eligibility rule to all operational modeling paths; keep test/scenario use explicitly separate. Acceptance: pending/rejected/error readings cannot drive operational advice, while an accepted correction can; regression coverage should include both paths.

### 2. Project lifecycle is incomplete — high priority, partly reproduced

Updating `date_fin_prevue` with a valid ISO date returned 500. `agents/mis/router.py:94` accepts an untyped dictionary and assigns strings directly to ORM attributes before committing. Related legacy update handlers use the same pattern.

The visible project cards offer creation and deletion but no edit or status transition. `frontend/src/api/mis.ts` exposes project list/create/delete hooks, with no project-update hook. A Kanban display cannot support normal project management if users cannot move a project from planned to active or completed.

Acceptance: users can edit dates and ownership and advance status in the UI; invalid edits return clear validation errors without corrupting records.

### 3. Scientific-watch failure can look like success — high priority, reproduced

A mocked RSS fetch exception resulted in a collection run with `status=completed`, `error_message=null`, and zero articles. The RSS service catches exceptions and returns an empty list (`agents/veille/services/scraper.py:78`), which the agent treats as a successful empty fetch. Separately, an embedding failure is treated as a skipped item (`agents/veille/agent.py:143`), potentially hiding why nothing was collected.

Acceptance: source failures and enrichment failures appear in the run result and UI; users can distinguish “no new papers” from “collection failed.”

### 4. Invalid parcel parameters are accepted — high priority, reproduced

The parcel API accepted negative area, latitude 999 and field capacity below the wilting point, returning 200. `ParcelCreate` in `agents/digitaltwin/schemas.py:9` has no domain bounds or cross-field checks.

Acceptance: positive area, valid coordinates and a physically consistent soil-water range are validated at the API boundary, regardless of frontend form constraints.

### 5. Submission claims exceed available evidence — high project priority

The local `multiagent.db` contains one project, zero researchers, zero watch sources/articles, zero parcels/readings, and zero simulation/optimization/calibration runs. The separate demo database has eight readings, all explicitly marked `demo`, and no calibration profiles. This is not proof that real data exists nowhere; it is proof that these supplied databases cannot substantiate field validation.

Calibration chooses parameters using RMSE over the same observations reported as `validation_observations` (`agents/digitaltwin/services/calibration.py`). That is fitting evidence, not independent predictive validation. The UI does disclose field-capacity identifiability, which is a useful safeguard. Document crop coefficients, input units, measurement timing and model assumptions; label fitting metrics correctly. For scientific claims, add an independently evaluated real dataset and a baseline comparison. If real data cannot be obtained before the deadline, report that limitation and restrict the evaluation to software correctness.

### 6. Agent and AI descriptions need precision

The MIS agent's subscription setup is `pass`, and its handler only prints (`agents/mis/agent.py:21`). MIS routers do publish events and implement useful operational logic, so the module is not fake; calling it an autonomous event-processing agent is inaccurate. Simulation and optimization are on-demand modules. The floating assistant uses keyword matching and workspace data in the frontend, not general conversational RAG.

Describe the actual mechanisms and your contribution to integration. Do not make “eight autonomous AI agents” the central achievement unless that claim is backed by observable behavior.

### 7. The handover package is not yet trustworthy

Before this audit, **32 tracked files were modified**, with approximately 3,590 added lines and 327 removed lines, plus untracked application code and migrations. The current app therefore differs materially from committed HEAD. Sending only the repository's committed state can omit demonstrated features.

`CLAUDE.md`, `HANDOFF.md`, `CAPACITES-ET-ROADMAP.md` and the newer operator guide disagree about capabilities, operation count, persistence and remaining work. The frontend README is still a Figma bundle starter. No root README or maintained automated regression/CI setup was found. The old handoff also reports an exposed historical ScraperAPI credential; rotation status was not independently established.

Acceptance: a complete reviewed commit or archive, one current installation guide, a documented version/runtime, a fresh-checkout smoke test, a capability matrix and a known-limitations list. Confirm the historical credential issue is resolved before sharing source history. Do not bundle local secrets or runtime databases by accident.

## Product and presentation assessment

The UI provides a coherent visual foundation, meaningful creation forms, an onboarding checklist and a useful cross-module activity timeline. These help explain the integrated workflow.

The first impression is less precise than the newer operator guide: welcome/home copy promotes “World-Class Scientific Ecosystem,” “GIS intelligence,” “Live IoT Grid” and “8 AI Agents.” The home footer uses generic LabAI branding, a 2024 copyright and legal labels; align identity and links with the actual laboratory. The dashboard displays hardcoded zero-percent change indicators despite having no trend calculation (`App.tsx:752`). Remove unsupported indicators rather than invite questions about their meaning.

Keep unfinished modules clearly labeled as planned or grouped separately. Put setup links beside operational blockers: “No budget linked” should lead to budget creation rather than require discovering Administration. Existing role-aware public curation is useful, but the documented viewer role is not in the implemented auth role union; both backend and frontend normalize unknown roles to researcher. Decide and document the actual access model before a real rollout.

The backend correctly bases roles on server-controlled `app_metadata` rather than user-editable metadata. This matches the distinction in the [Supabase user documentation](https://supabase.com/docs/guides/auth/users). This source supports that narrow observation, not a security certification of the deployed project.

## Focused submission plan

1. Agree a one-page internship scope mapped to the original cahier: delivered, partial and deferred. Record approval of architectural substitutions such as FastAPI/Supabase and the parcel-only model.
2. Fix the quality bypass, project lifecycle/date editing, collection error reporting and parcel validation. Add regression checks for the reproduced failures and the successful approval chain.
3. Prepare one reproducible case: project → parcel → measurement → quality review → advice → human approval → recorded application → activity history. Use authorized real records where available; explicitly labeled test data is suitable for software demonstration, never field-validation claims.
4. Prepare one real literature/profile example with source identifiers and reviewed output; keep network-dependent collection out of the live presentation until preflight succeeds.
5. Reconcile the interface copy and documentation, simplify planned navigation, and explain remaining limitations openly.
6. Verify the exact submission artifact on a clean checkout and package an architecture diagram, setup guide, evaluation results, demo script and concise future-work list. Explain original contributions versus pre-merge contributors and generated UI assets.

For a ten-minute presentation, spend most time showing the complete workflow and explaining one design decision and one measured limitation. A short, reliable demonstration with honest evaluation is a stronger final deliverable than a tour of every menu item.

**Final decision:** suitable as a substantial internship MVP after a bounded completion pass. The next work should make the existing workflows reliable and defensible, rather than expand the feature count.
