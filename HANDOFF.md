# Session handoff — "make the platform actually work"

Last updated: 2026-07-30. Keep this file current at the end of every session so a
fresh session can resume without replaying the whole conversation.

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

1. **MIS sub-resource create hooks are unwired.** `useCreatePersonnel`,
   `useCreateEquipement` and `useCreateBudget` exist in `frontend/src/api/mis.ts` and are
   imported nowhere — the same gap that hid the four flows fixed on 2026-07-30. The
   `Modal`/`Field`/`FormError`/`SubmitButton` primitives make each one a small form.
2. **`VisitorPortalPage` `searchSuggestions`** — static prompt strings. Harmless (they
   are placeholder copy, not data) but not backed by anything; consider deriving them
   from real article tags.
3. **`WelcomePage` footer copy** — not yet audited for further invented claims.
4. **Audit the veille router auth comments** before any deployment: several endpoints
   carry "No auth required for dev testing" comments despite the global
   `Depends(get_current_user)`.
5. **Celery decision:** tasks.py files were removed (dead code — no Celery app existed).
   `celery` stays in requirements. Decide: stand up a real Celery worker for
   background tasks, or remove `celery` from requirements entirely.
6. **Scope-honesty pass** (Tier 2): the platform's simulation is a FAO-56 water-balance
   bucket (not SWAT/HEC-HMS/EPANET); optimisation is a greedy threshold scheduler (not
   Bayesian/GA). Rename/reframe to match reality, or implement the promised engines.
7. **Missing data sources** (Tier 2): add ArXiv + PubMed fetchers to veille (only
   RSS/Atom exists); implement Scopus fetch (column exists, no fetch code).
8. **pgvector activation** (Tier 2): embeddings are stored as JSON with in-memory cosine
   loop. For >1000 articles, switch to Postgres + Vector column + `<=>` distance.

## Standing principle

No backend endpoint was fabricated. Where no data source exists (conversational RAG,
conferences, datasets, theses, news, user management, per-agent perf/confidence), the
code either does honest local computation, substitutes a genuinely-backed section, or
says "Not implemented yet" with the reason and the nearest real endpoint.