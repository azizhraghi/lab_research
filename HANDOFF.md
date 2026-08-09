# Session handoff — "make the platform actually work"

Last updated: 2026-08-09. Keep this file current at the end of every session so a
fresh session can resume without replaying the whole conversation.

## 2026-08-09 (later) — a mistyped reading can finally be retracted

Pending #1 is **done**, and it was the first backend write since the merge:
`DELETE /api/twin/parcels/{parcel_id}/readings/{reading_id}`
(`agents/digitaltwin/router.py`, right after `add_reading`). 71 operations now,
and it is the **first delete route outside MIS**.

Design decisions worth keeping:
- **Roles mirror `add_reading`** (`researcher`, `reviewer`, `administrator`), not
  the narrower admin-only gate on `create_parcel`. Whoever can record an
  observation must be able to retract it — otherwise a typo is permanent for
  everyone who can actually enter data.
- **The lookup is scoped to the parcel in the path.** `db.get()` alone would let
  `DELETE /parcels/1/readings/{id-owned-by-parcel-2}` destroy another parcel's
  observation; the handler compares `reading.parcel_id` and 404s on mismatch.
- **The response is `SensorReadingDeleteResponse`, not a bare message** — it
  returns `was_latest` and `remaining` because `/recommend` reads exactly one
  row (newest by `recorded_at`). The UI needs to know whether it just changed
  the next recommendation.

Verified live against a booted API on :8011 (`DISABLE_AUTH=true`), then all
verification rows deleted — `twin_sensor_readings` and `twin_recommendations`
are back to 0, `twin_parcels` still 1:
- Non-latest delete → `was_latest:false, remaining:2`. Latest → `was_latest:true`.
- Re-deleting the same id → 404. Wrong parcel (`/parcels/99/readings/1`) → 404
  **and the row survived** (confirmed by re-listing).
- **The retraction actually moves the model**: a typo'd `35` (35 % read as
  35 mm) on top of a real `80` pushed the balance from `-44.27` to `-79.28`;
  deleting the typo restored `-44.27` exactly.
- Deleting the final row → `remaining:0`, and `/recommend` then 400s
  ("No sensor readings for parcel 1") as documented.

Two traps found while testing, both now surfaced in the UI:
- **Deleting a reading does not revise recommendations already stored.** There is
  no FK from `IrrigationRecommendation` to the reading it used, so the two
  `-79.28` rows from the typo outlived it. The confirm dialog warns when the
  target is the newest row, and the success banner prompts a re-run.
- **SQLite reuses freed ids** (`max(id)+1`), so a new reading took id 2 after
  ids 2 and 3 were deleted. Do not assume ids keep climbing when hand-testing;
  re-list before targeting an id. The CSV upsert key is still
  (parcel, `recorded_at`, `sensor_code`), so re-importing a file recreates a
  deleted row — correct upsert behaviour, but surprising after a cleanup.

Frontend: `useDeleteReading` + `SensorReadingDeleteResult` in
`frontend/src/api/digitaltwin.ts`; a per-row trash button in the IoTPage
"Recorded Readings" table (new "Correct" column) reusing the existing `Modal` /
`FormError` / `Trash2` pattern from the MIS project delete. `npm run typecheck`
clean, `npm run build` clean (2317 modules).

## 2026-08-09 — the water loop is now reachable (`c142486`)

`twin_sensor_readings` is no longer write-only-in-theory. `IoTPage` can enter a
reading by hand, bulk-import a CSV, and generate a real irrigation figure. This
was Pending #1 and it is **done**; frontend only, no backend endpoint changed.

What was verified against a live backend (not inferred):
- Manual POST round-trips a naive timestamp unshifted (`2026-08-09T06:00` →
  `2026-08-09T06:00:00`). Send naive local time; do **not** append `Z`.
- CSV import: `created:3`, then `updated:3` on re-import — upsert key is
  (parcel, `recorded_at`, `sensor_code`). A missing column 400s and names it. A
  bad row is rejected individually while the good rows still commit.
- 60 mm on the 45/120 parcel → **42.0 mm** at score 0.69; 115 mm → **0.0 mm** at
  0.90. Both reproduce the model by hand.
- `/recommend` reads **exactly one row** — the newest by `recorded_at`. Importing
  back-dated history does not change the answer. It 400s (not 404) at zero rows.
- Verification rows were deleted afterwards; both twin tables are back to 0.

Three traps worth keeping in mind:
- **`soil_moisture_mm` is root-zone storage in mm, not % VWC**, and the schema
  accepts any value `>= 0` with no upper bound. A "35" meaning 35 % is stored
  happily and silently poisons the recommendation. The form prints the parcel's
  own WP→FC band and warns outside it; the %→mm converter is opt-in, shows its
  arithmetic, and asks for root-zone depth rather than guessing (the `Parcel`
  model has no depth column).
- **`confidence` is not confidence.** It is `0.65 + 0.25 × stress_ratio` — a
  wetness index bounded to [0.65, 0.90]. A parched parcel scores *lowest*
  exactly when the advice matters most. The UI renders it as a "reserve score"
  with the formula visible. Do not relabel it "confidence".
- **`ParcelDetail.latest_readings` is server-capped at 30.** `IoTPage` used it
  for every average and chart, so the page was silently truncating. It now uses
  `GET /readings` with an explicit limit and states the window it covers.

Also fixed: FastAPI returns 422 `detail` as an **array** of `{loc, msg}`, which
`String()` rendered as `[object Object]`. `formatDetail` in
`frontend/src/lib/apiClient.ts` now formats it as `field: message` — this fixes
error display in *every* form in the app, not just the new ones.

## 2026-08-08 — the repo was not storing the project (READ THIS FIRST)

Before this session, **most of the live app had never been committed**. `git log`
HEAD was still `1679022`, and 114 files were untracked, including all of
`frontend/src/app/App.tsx` (4,356 lines), every `frontend/src/api/*.ts`,
`main.tsx`, `AuthContext.tsx`, the whole of `agents/mis/`, `agents/orchestrateur/`
and `agents/qualite/`, and the ArXiv/PubMed/Scopus fetchers. Meanwhile the files
git *did* track under `frontend/src/` were the superseded JSX prototype including
`mockData.js` — nothing the live app imports. A `git clean -fd` or a fresh clone
would have destroyed months of work.

Fixed in five commits (`b61c3a8` → `355c672`). Verified by cloning HEAD into a
temp dir: `tsc --noEmit` clean, `npm run build` clean (2317 modules), and
`from api.main import app` boots all 70 operations using only `.env.example`.

**Rules that follow from this:**
- Commit at the end of every session. The working tree is no longer allowed to
  drift from HEAD — that drift *was* the single biggest risk in the project.
- `data/` and `cvs/` are now gitignored: runtime state the app recreates, not
  source. `data/researchers.json` held fabricated seed profiles ("Dr. Amina
  Benali", h-index 12, publications "Attention Is All You Need" / BERT) feeding
  the legacy `/api/biblio/profiles/*` endpoints. That system is still live and
  still slated for removal — see Pending #1.
- The pre-merge folders are now gitignored and kept on disk for reference only.

### ⚠️ Exposed credential — needs rotation

`Research-Lab-Platform/test_scholar.py` contains a hardcoded ScraperAPI key
(`API_KEY = "ff8101b9..."`) committed in `1679022`, which is **already pushed to
a public GitHub repo** (`github.com/azizhraghi/lab_research`). Deleting the file
does not help — the key remains in history at that commit. **It must be rotated
in the ScraperAPI dashboard.** Nothing else leaked: `.env` has never been
committed, and a secret scan of all 114 newly-committed files came back clean.

### Corrections to the previous audit

Verified against the actual repo; several claims did not hold:
- "8 articles with real content in DB" → **2**. 19 of 27 tables are empty: 0
  projets, 0 personnels, 0 budgets, 0 alertes, 0 rapports, 0 simulation_runs,
  0 optimisation_runs. So "live-tested every endpoint" cannot be right.
- **`twin_sensor_readings` = 0.** The FAO-56 water balance, calibration
  grid-search and irrigation scheduler are all real code that has **never run on
  real data**, and there is no UI to enter a reading. For a water lab this is the
  most important gap in the platform — bigger than any cross-agent wiring.
- "Dead folder cleanup ✅ DONE (git and disk)" → they were staged but never
  committed, and both are still on disk.
- Tier A #1 (wire the 5 orphan hooks) was **already done**. Only
  `useResearcherCvUrl` (a URL helper) and `useRunTwinSimulation` (superseded)
  are unreferenced, neither of which is a gap.

## The task

Full platform audit + Tier 1 fixes: make every backend endpoint work, wire the
event bus so agents actually communicate, and persist all state that was
ephemeral. Frontend honesty work (previous session) is complete; this session
was backend-only.

Follow-up (2026-07-30): after the cleanup the user reported pages looking "broken".
That did **not** mean missing data — it meant missing *write* UI: no add-parcel /
add-project button, no way to add a researcher, and a Trigger-scrape button where
"nothing happens". Root cause: the merge brought in the API-client layer
(`frontend/src/api/*.ts`) but not the UI that calls it — every create hook existed and
none were imported into `App.tsx` except `useTriggerScrape` and `useSyncResearcher`.
The fix was real forms on real endpoints, with **no** fabricated data. Do not respond
to "broken/blank" by re-adding mock rows; check whether the create path is wired.

Guard: `npm run typecheck` (`tsc --noEmit`) from `frontend/` after every change.
There is no lint script — `frontend/package.json` has only `build`, `dev`, `typecheck`.

Almost all remaining work is in one file: [frontend/src/app/App.tsx](frontend/src/app/App.tsx)
(all pages, routing, and any leftover mock data live there).

## Ground rules learned the hard way

- **Backend agent identifiers** (each agent's `name`, and the `source_agent` on every
  event): `veille`, `bibliometrie`, `digital_twin` (underscore — dir is `digitaltwin`,
  API prefix is `/api/twin`), `simulation`, `optimisation`, `mis`, `qualite`,
  `orchestrateur`. Gateway prefixes do not always match directory names
  (`/api/biblio` for bibliometrie).
- **Orchestrator history is in-memory and arrival-ordered.** `_historique` is appended
  newest-LAST and lives on the API process, so it resets on restart. Any "recent"
  view must `[...list].reverse()` first.
- **No agent lifecycle endpoints exist.** A full sweep of `@router.*` decorators
  confirmed there is no start/pause/run-agent route. The only argument-free trigger
  is `POST /api/veille/trigger`.
- **lucide-react icon imports shadow JS globals.** `Map` is imported as an icon, so
  `new Map<K,V>()` will not compile — use `Record<string, number>` + `Object.entries`.
- `??=` is ES2021 but tsconfig `target` is ES2020 — use explicit if/else init.
- `noUnusedLocals` / `noUnusedParameters` are on: deleting a UI feature also means
  deleting its icon imports and its state, or the build fails (hit this twice, with
  `Pause` and `UserPlus`).
- Bibliometrie computes exactly three indicators (`agents/bibliometrie/services/indicators.py`):
  `h_index`, `i10_index`, `total_citations`. `ResearcherResponse` carries **no**
  publications list — labelling i10 as "Publications" was wrong.
- Qualité `_calculer_niveau`: 0 problems → `conforme`, ≤2 → `avertissement`, else
  `non_conforme`. `conforme_rgpd` only varies in `valider_personnel`.
- **Language split** across the merged repo: veille / bibliometrie / digitaltwin types
  are English; MIS / orchestrateur / qualite types are French (`nom`, `statut`,
  `budget_alloue`, `evenements_traites`, `niveau`, `problemes`).
- The backend exposes **no** RAG/chat endpoint, no per-agent perf/confidence
  telemetry, and no models for conferences, datasets, theses, news, or user management.
- **`POST /api/veille/trigger` is argument-free by design.** There is no search term
  anywhere in the path: `run_collection()` (`agents/veille/agent.py`) selects
  `Source.active == True` and iterates those rows. With zero active sources a run
  genuinely does nothing. It also only handles `source.type in ("rss", "atom")` — any
  other type is stored, silently skipped, and never gets `last_scraped` stamped. The
  user's "I don't know what subject it scrapes" was a real product gap, not confusion.
- **`POST /api/biblio/researchers/{id}/sync` always 500s.** `agents/bibliometrie/router.py`
  calls `run_sync_for_researcher`, which is defined on neither `BibliometrieAgent` nor
  `BaseAgent`. Unfixed (no backend edit was made); the UI surfaces the error instead of
  promising a sync.
- Do not edit the pre-merge sibling folders (`AI Research Laboratory Platform/`,
  `research-lab-agents/`, `Research-Lab-Platform/`) — changes there never reach the
  running app.

## Done

All in `frontend/src/app/App.tsx` unless stated otherwise.

- **`agents` registry** — replaced 8 objects of fabricated telemetry (`confidence`,
  `perf`, fake uptime) with a typed registry keyed to the real backend agent `name`
  values, each carrying its real `endpoint` and the `Page` it links to.
- **`AgentsPage`** — now `AgentsPage({ setPage })`. Groups `useHistorique()` into
  `Record<string, HistoriqueEvenement[]>` by `source_agent` to derive real per-agent
  event counts, an Active/Idle badge (orchestrateur uses `/status` instead), the last
  routed event type with a relative-time formatter, real endpoint labels, the last 4
  real events (`events.slice(-4).reverse()`) with `alertes_generees.length`, an
  "Open module" button and a veille-only Trigger button. Fake `Processing batch
  847/1200` log and the dead Run/Pause buttons are gone. An `Info` disclaimer states
  the counts are in-memory and reset on API restart.
- **New `AdminPage`** replacing the Administration placeholder — surfaces the Qualité
  agent, which was previously reachable from nowhere in the UI. Four-family tab bar
  (`projet` / `personnel` / `equipement` / `budget`) built from real MIS rows, a
  per-row Validate button wired to the new mutation, latest-verdict badges, a reports
  feed with `problemes` bullet lists and a GDPR line for `entite_type === "personnel"`,
  plus a "Session & Access" grid of real auth values (`user.email`, `user.role`,
  `user.id`, `API_BASE_URL`, auth mode, token presence) and a dev-bypass warning
  naming `VITE_SUPABASE_*` / `DISABLE_AUTH`.
- **`frontend/src/api/qualite.ts`** — rewritten. The file existed but was imported
  nowhere. Added the typed `QualiteStatus` shape, the `QualiteEntite` union, and the
  missing `useValiderEntite()` mutation (`POST /api/qualite/valider/{entite}/{id}`,
  invalidating both `["qualite","rapports"]` and `["qualite","status"]`).
- **`WelcomePage` login** — the fake gate (`setTimeout(1200)` accepting any email, or
  the literal password `admin`) now calls the real Supabase `signIn` from
  `AuthContext`, short-circuiting when `devBypass` is on rather than pretending to
  verify. This was the most direct answer to "the supabase work i've done isn't there".
- **`WelcomePage` dead copy** — removed the "Demo tip: Enter any email + any password"
  note (actively false after the change above), the dead "Forgot password?" control,
  the dead "Sign in with Google Workspace" SSO button, and the invented `v3.2.0`
  version strings.
- **`PlaceholderPage`** — gained a required `missing: string` prop and lost its dead
  "Explore Module" button. Each of the five remaining placeholders now renders
  "Not implemented yet — {reason}" naming the real alternative endpoint. The
  fabricated "156 curated datasets" is deleted.
- **`ProjectsPage` timeline** — bars were `left: i*5%` / `width: 80 - i*5%`. Now
  computed from real `date_debut` / `date_fin_prevue` against the min/max window, with
  a real date-range subtitle, a `title` tooltip, and a "No valid start date" fallback.
- **`DashboardPage`** — fixed an ordering bug: "Recent Events" took the first five of
  an arrival-ordered list (i.e. the oldest). Now reverses first.
- **`PublicationsPage`** — tag chips derived from real tag frequency (top 8); the dead
  Export BibTeX button now builds real `@misc` entries from title/authors/year/doi/url/
  keywords and downloads a Blob, disabled when the filtered set is empty.
- **`HomePage`** — deleted the invented partner wall (`CNRS`, `MIT`, `WHO`, …) and
  replaced it with "Literature Sources Monitored by the Watch Agent" from real
  `useSources()`, including an empty state naming `POST /api/veille/sources`.
- **`VisitorPortalPage` researchers** — mapped from real profiles only. Removed
  invented `institution`, `country`, `skills`, `active`, `following` and the fake
  citation-trend sparkline array. Added real department facets, working search, a
  metrics-provenance line, an Identifiers grid (ORCID / Scholar / Scopus, or "not on
  file"), a real `mailto:` contact, real ORCID/Scholar deep links (disabled spans when
  absent), and the real CV link `${API_BASE_URL}/api/biblio/researchers/{id}/cv/pdf`.
  "View all 84 →" became a real "{n} of {m} shown". Follow buttons removed (there is
  no social graph in the backend). "Pubs" relabelled "i10".

### 2026-07-30 — the missing create UI

- **Shared form primitives** in `App.tsx`, reuse these rather than inventing more:
  `Modal` (line 239 — fixed overlay, backdrop click + Escape close, `max-w-lg`),
  `Field` (270 — label + hint + required asterisk), `FormError` (287 — renders
  `error instanceof Error ? error.message : String(error)`), `SubmitButton` (298 —
  `Loader2` spin while pending, else `Plus`). Inputs share the `inputCls` constant.
- **Four create flows**, each posting to an endpoint that already existed:
  new project (`POST /api/mis/projets/`), new researcher (`POST /api/biblio/researchers`),
  new parcel (`POST /api/twin/parcels`), new watch source (`POST /api/veille/sources`).
  Two are extracted named components — **`NewProjectForm`** (declared 794) and
  **`AddSourceForm`** (declared 2187, used 2352). The other two are inline inside their
  page components: researcher at **1182**, parcel at **1570**. There are no
  `AddProjectForm` / `AddResearcherForm` / `AddParcelForm` symbols — do not hunt for them.
- **Create hooks wired** into `App.tsx` imports (lines 28–41): `useCreateSource`,
  `useCreateResearcher`, `useCreateProjet`, `useCreateParcel`. They all existed in
  `frontend/src/api/*.ts` and were imported nowhere.
- **`frontend/src/api/digitaltwin.ts`** — added `useCreateParcel` (the one create hook
  that did not exist at all): `POST /api/twin/parcels`, invalidates the parcels query.
- **`frontend/src/api/veille.ts`** — widened `useCreateSource`'s param type to include
  `config?` and `active?`, mirroring `SourceCreate` in `agents/veille/schemas.py`.
  Without this the form's `active` flag was a TS2353 ("object literal may only specify
  known properties"). Mutation param types must mirror the pydantic schema exactly.
- **`WatchPage` honesty pass** — a "Configured sources" panel stating "A scrape has no
  search box — it fetches every active source below", an `{active} active / {total}`
  count, an amber warning at zero sources, per-source rows (name, url, type badge,
  active/paused badge, `last_scraped` or "never run"), and the trigger button now
  renders `trigger.isError` via `FormError` and `trigger.isSuccess` as "Collection run
  finished. New articles appear in the feed below; duplicates are skipped." It is
  disabled at zero active sources with a `title` explaining why. Previously neither the
  error nor the result was rendered, so a 403/500 was swallowed — literally the
  reported "nothing happens".
- **Verified clean**: `npm run typecheck` (`tsc --noEmit`) → no errors, and
  `npm run build` → `✓ built in 12.52s`, 2317 modules, JS 994.40 kB (gzip 267.40 kB),
  CSS 143.40 kB (gzip 20.73 kB). The only warning is Vite's pre-existing ">500 kB
  chunk" advisory, not introduced by these edits.

## Pending — start here next session

Ordered by value to LRSTE, not by effort. Previously-listed items now **done**:
MIS sub-resource create hooks, `searchSuggestions`, the ArXiv/PubMed/Scopus
fetchers, pgvector dedup, the sensor-reading ingestion UI, and (2026-08-09)
the reading-delete route.

1. **The rest of the water workflow is still unreachable from the UI**, though
   the backend is complete and now has data to work on:
   `POST /parcels/{id}/irrigation-events` (log what was actually applied — the
   only way to close the loop between advice and practice) and
   `/calibrations/run` + `/calibrations/{id}/apply` (fit this parcel's real
   parameters; needs >= 14 observations, and only rows flagged exactly `ok`
   with `data_origin` in {field, field_import} are eligible — which the new
   ingestion UI is careful to produce).
2. **Still no delete/edit on anything else.** The reading route above is the only
   non-MIS delete. There is still no `DELETE /api/veille/sources/{id}` and no
   `PUT`/`DELETE` on researchers or parcels — and a parcel delete needs a
   decision on its children (readings, forecasts, irrigation events,
   calibrations, recommendations all FK to `twin_parcels` with no cascade
   configured, so a naive delete will fail or orphan rows). Follow the pattern
   set by the reading route: scope child lookups to the parent, and return what
   the caller needs to know rather than a bare message.
3. **Remove the legacy JSON profile system.** `/api/biblio/profiles/*` (6
   endpoints, `agents/bibliometrie/router.py:97-139`) is a parallel researcher
   store from pre-merge code, backed by the now-gitignored `data/researchers.json`
   of fabricated profiles. The DB-backed `/api/biblio/researchers` is the real one.
4. **`@app.on_event("startup")` is deprecated** (`api/main.py:46`) — migrate to a
   FastAPI lifespan handler.
5. **InMemory bus dispatches synchronously** inside the publisher's coroutine
   (`shared/event_bus.py:118`). Bibliometrie's Scholar call + PDF regeneration run
   *inside the HTTP request that triggered the scrape* — a request-timeout bug, not
   just a scaling note. Redis publish failures are also swallowed silently
   (`:56-58`, returns `""`), so `EVENT_BUS_TYPE=redis` without Redis running means
   agents stop communicating with no error anywhere.
6. **Audit the veille/biblio router auth comments** before any deployment: two
   endpoints carry "No auth required for dev testing" despite the global
   `Depends(get_current_user)`. Confirm `DISABLE_AUTH=false` in prod — it returns
   an `administrator` stub to every caller.
7. **Celery decision:** `celery>=5.4.0` is still in `requirements/base.txt` with no
   Celery app (the dead `tasks.py` files are now deleted). Stand up a real worker
   or drop the dependency.
8. **Dependencies are unpinned** (`>=` throughout, no lockfile) — builds are not
   reproducible across machines.
9. **Scope-honesty pass:** simulation is a FAO-56 water-balance bucket (not
   SWAT/HEC-HMS/EPANET); optimisation is a constrained greedy scheduler (not
   Bayesian/GA). Both are legitimate, useful tools for irrigation scheduling —
   recommend relabelling the cahier des charges rather than promising engines the
   lab likely does not need. Relabelling is a day; real engines are months.
10. **MIS/DigitalTwin/Simulation/Optimisation subscribe to nothing**
    (`_setup_subscriptions` is `pass`). They are REST-only services, so creating a
    project does not auto-create a parcel or trigger a run. The "multi-agent" claim
    holds for 4 of 8 agents.

## Standing principle

No backend endpoint was fabricated. Where no data source exists (conversational RAG,
conferences, datasets, theses, news, user management, per-agent perf/confidence), the
code either does honest local computation, substitutes a genuinely-backed section, or
says "Not implemented yet" with the reason and the nearest real endpoint.