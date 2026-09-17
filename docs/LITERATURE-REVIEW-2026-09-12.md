# Topic-based literature review — 12 September 2026

Scientific Watch now supports a complete private screening workflow: enter a PubMed query, retrieve available abstracts, inspect source evidence, save an inclusion/exclusion decision with an annotation, and export an annotated text bibliography of included papers.

## Walkthrough

1. Apply `alembic upgrade head` before starting the backend. This adds `veille_literature_reviews`.
2. Sign in as a researcher, reviewer or administrator; open Scientific Watch.
3. In Literature review workspace, enter a topic such as `water quality monitoring` and select Start review. The UI requests at most 10 records (API maximum 20).
4. Inspect the original-source link, DOI and complete retrieved abstract. The short evidence panel is a verbatim excerpt, not an AI synthesis. Literal keyword matches explain retrieval overlap, not scientific relevance or quality.
5. Select Include or Exclude, add an annotation and Save review. Each topic retains its own decisions; collection does not silently change decisions in an earlier review.
6. Export annotated bibliography. Only included papers appear, with source links, metadata, source excerpts and saved notes. At least one inclusion is required.

## Boundaries and persistence

Reviews belong to the authenticated account. API queries enforce ownership, and the frontend query cache is scoped to account ID. Viewer accounts cannot create reviews or change decisions. PostgreSQL migration enables RLS without browser-facing policies; application access requires the trusted backend connection described in the deployment guide. PostgreSQL deployment itself was not tested in this pass.

These are private source snapshots, separate from the shared Article feed and its subscription/digest states. They do not add publications to researcher profiles or constitute laboratory approval. DOI/URL duplicates are removed within each review. The latest 50 reviews are listed.

Collection uses PubMed ESearch followed by EFetch XML, preserving structured abstract section labels. Missing abstracts are explicitly marked metadata-only. Source failures persist as failed reviews rather than empty successful results. An interrupted process can leave a collecting record; restart collection as a new review. Background recovery, pagination beyond 50 reviews and team review are not implemented.

No full-text appraisal, exhaustive systematic search, validated relevance ranking, citation metrics or generated scientific synthesis is claimed. Journal issue dates can be in the future for advance publication; partial dates use approximate month/day values. The complete AI enrichment/digest chain remains a separate live-validation task.

## Verification

- 24 offline regression tests passed, including migrated temporary database setup, structured XML parsing, DOI deduplication, missing abstracts, persistence, inclusion-only export, account isolation, viewer permissions and collection failures.
- TypeScript check and production build passed. Vite retains its existing large-bundle warning.
- `python scripts/verify_literature_review.py` performed a live public-source/API check in a temporary database: query `water quality monitoring`, three records, three abstracts, one saved inclusion and one exported item. No source mocking is used in this script.
- Live evidence metadata is recorded in `literature-review-2026-09-12-evidence.json`. The generated source snapshot and text export are local ignored artifacts under `tmp/integration-evidence/`.
- Browser check used an isolated database: blocked network access displayed an explicit failure; replay of the captured live records displayed abstracts, saved an annotation and inclusion, updated counts and enabled export. The browser export control was invoked; the saved browser download file was not inspected. The equivalent API-generated text export was inspected separately.
- Browser screenshot inspection confirmed readable layout and source-evidence labels at desktop size. Mobile layout and multi-user PostgreSQL concurrency were not tested.

No laboratory database was modified and no real lab measurements are needed for this workflow. Scientific usefulness still requires researcher screening of the retrieved publications.
