# Session handoff — "make the platform actually work"

Last updated: 2026-08-23. Keep this file current at the end of every session so a
fresh session can resume without replaying the whole conversation.

## 2026-08-23 (latest) — bus off the request path, computed quality flags, leadership doc

Three items from the refreshed pending list. Operation count unchanged
(**79**) — all three were behaviour fixes, not new routes.

- **InMemory bus dispatch moved off the request path** (old pending #1).
  Publish used to await every handler inline, so bibliometrie's Scholar fetch
  ran *inside* the HTTP request that triggered the scrape. Publish now
  enqueues to a single background FIFO worker: publish returns in ~0.5ms
  regardless of handler runtime; handlers still run in subscription order
  (qualite persists before the twin reacts — what the guarded startup relies
  on); handler exceptions are logged, never kill the worker; a dead worker
  restarts on next publish; history capped at 500 (was unbounded).
  RedisStreamsEventBus.publish now **raises** on failure instead of printing
  and returning "" — a dropped event means agents silently miss work; the
  consumer loop logs loudly and keeps polling, CancelledError propagates.
  Verified: unit test (non-blocking, order, error containment) + live chain
  (trigger 0.16s request, veille→biblio link landed exactly once).
- **`quality_flag` is now computed, not echoed** (old pending #3). New
  `agents/qualite/services/anomaly.py`: physical ranges (negative impossible —
  partly redundant with the API schema, kept for non-HTTP writers; moisture
  > 1.5× field capacity suspect, > 400mm error; rain > 200mm / ET > 20mm
  suspect; temperature outside [-30, 55]°C error; future timestamp error) and
  rate-of-change (moisture rise > rain + same-day logged irrigation + 10mm
  margin → suspect — the FAO-56 balance as a sanity check; catches unlogged
  applications). Verdict `ok|suspect|error` is written back onto the reading
  row, so the recommendation gate, the calibrator and the UI badges share one
  truth; only `ok` emits `twin.reading_validated`. Verified live: clean → ok
  → auto-recommendation; 70→110mm jump no water → suspect, no recommendation;
  450mm → error.
- **`docs/CAPACITES-ET-ROADMAP.md`** (old pending #4) — the scope-honesty
  one-pager in French for lab leadership: verified capabilities, the honest
  "what this is NOT" table vs the cahier des charges, known operational
  limits, phased roadmap, and the two decisions leadership owns (hydrological
  engines vs relabelling; RGPD policy).

## 2026-08-22 — audit-driven quick wins: deletes, honesty fixes, Scholar ETL

Started by committing the previous session's uncommitted planning/linking work
(as-is, 81 ops), then worked the audit's priority list. Operation count
**81 → 79** (6 legacy routes removed, 5 real ones added).

- **404 on missing parents** — `GET /readings`, `/irrigation-events`,
  `/calibrations` returned `[]` + 200 for a parcel that doesn't exist. Now 404,
  so "empty" means "no data" again. (Retires pending #4.)
- **`/recommend` honours calibration** — it read the static CROP_COEFFICIENTS
  table while simulation/optimisation used `get_active_crop_coefficient`;
  applying a calibration now moves the headline number too. (Retires #5.)
- **CV PDFs stop leaking files** — `tmp_cv_{id}.pdf` in the repo root, never
  deleted, not gitignored. Now `mkstemp` + `BackgroundTask(os.remove)`, with
  cleanup on the failure path too. (Retires #3.)
- **Scholar publication import** (`scholar_sync.py` was dead code, like ORCID
  once was) — reuses `upsert_works_for_researcher`; DOI-normalised dedup,
  shared rows, idempotent. One policy difference: Scholar *reports* citations,
  so its sync refreshes `citation_count` on matched rows; ORCID still never
  touches counts. Failed fetches raise `ScholarUnavailable` → 400 with the
  reason (rate-limit ≠ "no works"). Frontend: "Import from Scholar" button in
  the publications modal. (Retires #2.)
- **DELETE /veille/sources/{id}** — refuses with 409 + count while articles
  exist (parcel-delete contract). DELETE /biblio/researchers/{id} — refuses
  while publication links exist; indicators/CV profile go with the profile.
  PUT /biblio/researchers/{id} — partial update, UNIQUE collisions → 409
  naming the column. Frontend edit modal + confirm-guarded deletes.
  (Completes #1 alongside the earlier reading/parcel deletes.)
- **Legacy JSON profile system removed** (retires #6) — `/api/biblio/profiles/*`
  (6 endpoints), `data/researchers.json` (fabricated, deleted from disk), and
  the agent's JSON CRUD. The veille→biblio handler no longer appends to that
  dead file: an article **with a DOI** whose authors match DB researchers
  becomes a real `biblio_publications` row (source=veille) through the same
  upsert. DOI-less articles are skipped — an RSS title is not bibliographic
  evidence. Verified live: event → bus → linked row; re-fire → still 1 row.
- **Orchestrator `/trigger` publishes to the bus** instead of calling
  `handle_event` directly — manual triggers now exercise the full fanout path
  (this is how the veille→biblio chain was actually verified).
- **`@app.on_event` → lifespan** (retires #7); **celery dropped** from
  requirements + venv, nothing imported it (retires #10);
  **requirements/locked.txt** pins the exact environment (retires #11).
- Removed the last orphaned frontend hook (`useRunTwinSimulation`).

All verified live: boot clean (no deprecation warning), 6 agents start, 79
operations, tsc + vite build pass. Old pending #16 (orch history in-memory)
was already stale — history is DB-backed since 5f58e396ab57.

## 2026-08-21 — planning, alert context, and the MIS→twin chain

One uncommitted session's worth of work, audited (statically and live) and
committed as-is. Operation count **74 → 81**. Four features that close the loop
between management data and field work:

- **Task planning** (`agents/orchestrateur/planning.py` + `PlanningTaskDB` +
  `PlanningProposalDB` + 5 routes). Deterministic constraint heuristic — skills
  subset-match on `competences`, `disponible`, equipment `etat`, committed-work
  windows as hard constraints, pending work reserved only within one draft.
  Returns explicit conflicts ("No available person matches: X") instead of
  forcing an assignment. Proposals require human approval before a task moves
  `pending → planned`. Migration `h6b4e1c9a2d7`.
- **Alert context + dashboard actions.** `AlerteDB.context` (JSON, migration
  `e4c8f6a2d9b1`). `parcel_setup` alerts render a pre-filled New-Parcel modal;
  `irrigation_review` alerts hand off to the IoT page with the parcel focused.
- **MIS→twin wiring.** `POST /projets/` now emits `projet.created` after
  commit; the orchestrator turns it into a `parcel_setup` alert. Parcels gain a
  soft `project_id` link (indexed String, app-validated — migration
  `f2d7b4c1e8a6`) because MIS ids are UUIDs and hard FKs across agents were
  judged too rigid for now.
- **Reading→recommendation traceability.** Qualité now validates readings on
  `twin.reading_recorded` and emits `twin.reading_validated`; the twin agent
  auto-generates a recommendation (idempotent on `source_reading_id`, migration
  `d1f4e2a9b3c7`) which raises an `irrigation_review` alert; approving then
  logging the irrigation resolves the alert. Irrigation events can now cite the
  recommendation they executed (migration `g3a9c8d2e1f4`).

Live chain verified end to end before commit: reading → validation → auto
recommendation (`generation_mode="automatic"`) → orange alert → 409 on
apply-before-approve → approve → apply → alert auto-resolved.

Known asymmetry (deliberate, documented in `schemas.py:226`): migration
`d1f4e2a9b3c7` has no FK on `source_reading_id` while the ORM declares one —
traceability is app-enforced. Four of the five previously-orphaned frontend
hooks are now wired; `useRunTwinSimulation` remains (dead code, superseded by
`/api/simulation`).

## 2026-08-10 — ORCID publications ETL + parcel delete

Two features, both chosen by the user after an audit of the cahier des charges.
Operation count **71 → 74**.

**The audit finding that drove this: `biblio_publications` had no writer
anywhere in application code.** The only `Publication(...)` insert was
`seed_dev.py:125` (fabricated ML papers). `run_sync_for_researcher` writes only
`BiblioIndicator` rows; the `Publication` at `agent.py:469` is the pydantic class
from `agent.py:47` belonging to the legacy JSON store, not the ORM model.
`download_cv_pdf` queries that table at `router.py:60`, so **every CV ever
generated claimed the researcher had no publications.** ORCID sync is now the
table's first real writer.

`agents/bibliometrie/services/orcid_sync.py` was dead code (imported nowhere,
referenced only in `implementation_plan.md`); rewritten and wired.
`scholar_sync.py` is still dead — same shape, next candidate.

Backend: `orcid_sync.py` (rewritten), `publication_sync.py` (new),
`schemas.py` (+`OrcidSyncResponse`), `router.py` (+2 routes),
`cv_generator.py` (`_Pub`/`_MinimalResearcher` promoted to module level).
Frontend: `OrcidSyncResult` in `types.ts`, `useResearcherPublications` /
`useSyncPublications` in `api/biblio.ts`, `ResearcherPublicationsModal`
(`App.tsx:1333`) behind a new "Publications" button on each researcher card.

**Two ORCID API shape facts, verified live before coding** — the pre-existing
parser got both wrong:

- **`group` is already deduplicated.** ORCID clusters the same work asserted by
  several sources into one group holding multiple `work-summary` entries. Group 0
  of the Carberry record carried the same title twice (Crossref + the author).
  Iterate groups, take `summaries[0]`; iterating summaries double-counts.
- **Nulls are present-with-null, not absent.** `publication-date`,
  `journal-title`, `title.title` and `url` all exist with `None` values, so
  `dict.get(k, {})` returns `None` and a chained `.get()` raises
  `AttributeError`. Hence `_dig`/`_value`, which tolerate `None` at any level.

Design decisions worth keeping:

- **DOI is the dedup key, normalised** (lowercase, strip `https://doi.org/`,
  `http://doi.org/`, `doi:`, trailing `/`). Necessary because `Publication.doi`
  is `unique=True` and the same paper arrives as `10.1234/ABC` and
  `https://doi.org/10.1234/abc` from different asserting sources. Verified:
  `https://doi.org/10.1109/TPS.1987.4316723` → `10.1109/tps.1987.4316723`.
- **Co-authorship is a link, not a copy.** Publications are shared rows;
  authorship lives in `biblio_researcher_publications` (composite PK). Two
  co-authors syncing one paper → one publication row, two links.
- **`citation_count` is never written by ORCID sync.** ORCID reports no
  citations; writing 0 would destroy Scopus/Scholar data. `_enrich` only fills
  columns currently `None`.
- **`author_position` is left `None`.** ORCID work summaries do not expose
  author order, and inventing `1` would assert first authorship.
- **`OrcidUnavailable` → 400, not 500.** The request was well-formed; the
  upstream record is the problem. Distinguishes an outage from "no works".

Verified live against the real public API (no key required), then all rows
removed — DB back to 1 researcher / 0 publications / 1 parcel:

| Check | Result |
|---|---|
| First sync (`0000-0002-1825-0097`) | 6 works → 6 created, 6 links |
| Re-sync | 0 created, 6 already present — exactly idempotent |
| Co-author, distinct iD, shared DOI | 1 created, 1 enriched, **2 links** |
| No ORCID on file / nonexistent iD | 400, message names researcher / iD |
| Unknown researcher (both routes) | 404, so `[]` means "no publications" |
| CV PDF | 200, 2,989 bytes, real `%PDF-` |
| Parcel delete with 1 child | 409 "still has 1 sensor readings" |
| Parcel delete once clean | 200, then GET 404 |

**`twin_parcels` has six child tables, not the five this file previously
claimed** — `twin_simulations` (`SimulationScenario`) was missing from the
earlier delete-route note. `delete_parcel` counts all six, most-precious-first,
and refuses rather than cascading so field measurements cannot be lost by
mistake.

**Two traps for the next session:**

- **This FastAPI version does not flatten included routers into `app.routes`** —
  they stay as lazy `_IncludedRouter` wrappers, so counting `app.routes` reports
  5 and looks catastrophically broken. Count operations via
  `app.openapi()["paths"]` instead.
- **`biblio_researchers.orcid_id` is `unique=True`**, so two researchers cannot
  share an iD (correct — an iD identifies one person). Testing the co-author
  path needs two *distinct* iDs sharing a DOI, not one iD twice.

Git identity was `medaz <medaz@example.com>` repo-locally, overriding the
global `azizhraghi <azizhraghi@gmail.com>`. Since `example.com` is the
reserved placeholder domain, GitHub could not link those commits to any
account — they showed up as an unknown contributor. Fixed: repo-local
`user.name`/`user.email` now match the real identity, and the six unpushed
commits were reattributed via `git rebase origin/main --exec 'git commit
--amend --no-edit --author=...'` before pushing (fast-forward, no force).

**Still authored `medaz` and left alone: everything at or below `1507908`**,
which is already on the remote. Rewriting pushed history needs a force-push,
so that was deliberately not done. `git log origin/main --format='%an'`
currently shows 6 `azizhraghi`, 8 `aziz`, 7 `medaz` — all the same person,
but only the first two link to the GitHub account.

## 2026-08-09 (latest) — calibration: the water workflow is now complete

Pending #1 is **done**, and with it the whole water loop is reachable from the
UI: enter readings → log irrigation → fit a calibration → review it → apply it.
Both routes already existed; this session wired them, so the operation count
stays at 71. `CalibrationPanel` (`App.tsx:2882`, rendered at `:3429`) plus
`useCalibrations` / `useRunCalibration` / `useApplyCalibration` in
`frontend/src/api/digitaltwin.ts` and `CalibrationProfile` in `types.ts`. A new
`Stat` primitive (`App.tsx:301`) is shared by the result grids — reuse it.

**The fitter was checked for parameter recovery, not for HTTP 200.** Readings
were generated forward from a known `kc`/`field_capacity` using the same water
balance the calibrator fits, so a correct fit has to return those numbers back.
`make_field_csv.py` (repo root, committed) builds that fixture and prints its own
ground truth; it is a test generator, not measurements — the header says so. The
CSV it writes is gitignored, being regenerable. Re-verified after the final edit
to the generator: import 21/21, then a run returned **kc 1.14, fc 126.0, RMSE
0.0** over 20 validation days — exactly the seeded truth.

Two findings that change how the result should be read:

- **Field capacity is only identifiable if the soil actually saturates in the
  window.** The first fit recovered `kc` exactly (RMSE 0.0) but left fc at the
  parcel default. That is not a bug: with no reading at capacity, every
  candidate above the wettest observation predicts identically, and the strict
  `<` at `calibration.py:105` keeps the lowest grid value. Adding saturating
  rain recovered **both** exactly (kc 1.14, fc 126.0). The panel says which of
  the two the window can support rather than implying a blanket "calibrated".
  Caveat worth keeping: a profile does not store the readings it was fitted on,
  so the UI re-derives this from readings that exist *now*.
- **Apply is asymmetric, and the asymmetry is unhelpful.** `apply` writes back
  only `field_capacity_mm` (`calibration.py:173-176`) — the parameter most often
  *un*identified — and leaves crop type and wilting point alone. The fitted crop
  coefficient reaches simulation and optimisation through
  `get_active_crop_coefficient`, but **never `/recommend`**, which still reads
  the static `CROP_COEFFICIENTS` table. So calibrating does not change the
  headline irrigation figure. The UI states both paths explicitly.

**Silent multi-sensor data loss found.** Two sensors reporting at identical
timestamps produced a suspiciously perfect fit: `calibration.py:61-64` keeps one
reading per calendar day using a strict `>`, so equal timestamps resolve by
insertion order and the other sensor's entire series is discarded without a
word. Surfaced as an amber `duplicateDays` warning in the panel, since a second
sensor otherwise looks like it should improve the fit.

Verified live on :8013, then every row removed (all four twin tables back to 0
except `twin_parcels` at 1, and the parcel restored to `field_capacity_mm`
120.0):
- Apply moved the parcel 120.0 → **126.0**; `wilting_point_mm` 45.0 and
  `crop_type` wheat untouched. Statuses went candidate → applied, with the two
  older profiles marked superseded.
- Re-applying → 400 "Only a candidate calibration profile can be applied".
  Unknown profile → 400 "Calibration profile not found". `reviewed_by: "A"` →
  422 (`min_length=2`).
- `min_observations` 30 against 21 readings → 400 carrying the message to show
  verbatim ("Demo, unknown, and synthetic readings are intentionally excluded").
  6 and 366 → 422. Run against a missing parcel → 404.
- **`GET /parcels/999/calibrations` → `[]` with HTTP 200** — same missing
  existence check as `list_irrigation_events`. Third route with this shape now.
- Role gate confirmed end to end: researcher runs but **cannot** apply (403
  "Your laboratory role does not permit this operation."); reviewer and
  administrator do both; viewer is denied both.

Trap when hand-testing: **apply the profile you just fitted.** Applying an older
id leaves the parcel unchanged and looks like the write-back is broken. Re-list
before targeting an id — and note the CSV upsert key includes `sensor_code`, so
changing the sensor code in the fixture creates a parallel series instead of
updating the old one (this is how the duplicate-day case was found).

Typecheck and build clean (2317 modules, JS 1,053.02 kB / gzip 280.30 kB, the
only warning Vite's pre-existing >500 kB advisory).

## 2026-08-09 (later still) — irrigation logging: what was applied, not advised

Pending #1 is **done**. `POST/GET /api/twin/parcels/{id}/irrigation-events` both
already existed on the backend and were reachable from nowhere; this session
wired them. No backend change was needed, so the operation count stays at 71.

**Why this came before calibration** (the other half of Pending #1): calibration
sums `IrrigationEvent` amounts per calendar day into the water balance it fits
(`services/calibration.py:75-88`). With no events logged, a run does not fail —
it silently fits parcel parameters against a balance missing every drop of
applied water. Logging is a *prerequisite* for a trustworthy calibration, not a
record kept alongside it.

**Correction to the note in the previous entry:** calibration needing ">= 14
observations" understates the requirement. `calibration.py:66-73` also rejects
any gap — `len(dates) != expected_days` demands one quality-checked reading for
**every calendar day** in an unbroken run. Fourteen readings scattered across a
month fails with "Fill measurement gaps before calibration". Confirmed live: a
run against 0 readings 400s on the count check first.

Verified live on :8012, all rows deleted afterwards (all four twin tables back
to 0 except `twin_parcels` at 1):
- The exact payload the form sends round-trips, timestamp unshifted
  (`2026-08-09T07:30` → `07:30:00`). Same naive-local convention as readings.
- Server bounds each return 422 naming the field: `amount_mm` 0 (`gt=0`), 501
  (`le=500`), `recorded_by` of 1 char (`min_length=2`). The form guards all
  three client-side, so these are what it prevents rather than what users hit.
- `notes: null` is accepted; POST to a missing parcel 404s.
- **GET on a nonexistent parcel returns `[]` with HTTP 200, not 404** —
  `list_irrigation_events` never checks the parcel exists, unlike the POST. An
  empty table is therefore not evidence the parcel is real.

UI: a "Log irrigation" button and modal on `IoTPage`, plus an "Irrigation
History" panel between the readings table and the data-quality flags. The panel
states plainly that these are the applications calibration sums, and that an
unlogged irrigation makes a parcel look like it loses water it received.
`useIrrigationEvents` / `useRecordIrrigation` in `frontend/src/api/digitaltwin.ts`,
`IrrigationEvent` in `frontend/src/api/types.ts`. Typecheck and build both clean
(2317 modules).

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
  still slated for removal — see Pending #6.
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
fetchers, pgvector dedup, the sensor-reading ingestion UI, the reading-delete
route, the irrigation-event log, the calibration UI (2026-08-09), the ORCID
publications ETL + parcel delete, and the commit reattribution (2026-08-10);
the 2026-08-22 session retired old pendings #1 (veille source delete,
researcher PUT/DELETE), #2 (Scholar ETL), #3 (CV temp files), #4 (list-route
404s), #5 (/recommend vs calibration), #6 (JSON profiles), #7 (lifespan),
#10 (celery) and #11 (unpinned deps).

Working tree is **clean** as of 2026-08-23; commits through `9a0343b`. The
2026-08-23 session retired old pendings #1 (bus dispatch), #3 (anomaly
detection) and #4 (leadership doc).

1. **Deploy on Postgres.** pgvector activation, the HNSW migration and the
   conditional ORM columns have never run against actual Postgres. The lab
   will outgrow SQLite on first multi-user week. Also resolves the one known
   ORM/migration asymmetry: `d1f4e2a9b3c7` omits the `source_reading_id` FK
   the ORM declares (SQLite enforces neither; Postgres enforces whatever the
   migration says).
2. **`agents/mis/agent.py` is still a 37-line print() shell.** The router is
   real; the cahier's MIS automations (reminders, budget-vs-deliverable
   checks) don't exist. The planning heuristic in orchestrateur is the model
   to copy: deterministic, constraints reported, human approves.
3. **Role-gating UX.** Buttons render for all users and 403 on click for
   insufficient roles (approve proposal, create parcel, apply calibration).
   Hide or disable them based on role once the frontend knows it. The
   frontend has no notion of the current user's role yet.
4. **No automated test suite.** Every chain is verified by documented manual
   procedures (see session entries); a regression suite on the water loop and
   the publication ETL is the prerequisite for daily lab dependence.
5. **Sensor ingestion endpoint for IoT gateways** — readings arrive via the
   UI (manual + CSV). An authenticated machine endpoint (API key per
   gateway, same anomaly pipeline) is the natural next step for real sensors.
6. **Bundle size.** ~1 MB JS, single chunk. Code-split by page when it
   matters; fine for an internal tool today.


## Standing principle

No backend endpoint was fabricated. Where no data source exists (conversational RAG,
conferences, datasets, theses, news, user management, per-agent perf/confidence), the
code either does honest local computation, substitutes a genuinely-backed section, or
says "Not implemented yet" with the reason and the nearest real endpoint.
