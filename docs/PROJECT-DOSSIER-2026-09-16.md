# Project research dossier — 16 September 2026

Historical first dossier milestone. The subsequent research release implements evidence-linked findings, evaluation records and preserved supervisor submissions. See SUPERVISOR-HANDOVER-2026-09-16.md and RESEARCH-RELEASE-OPERATIONS.md for current behavior; the future-work statements below describe the earlier milestone.

## Delivered workflow

Research Projects now connects the research narrative, selected scientific evidence and operational progress. Under Laboratory operations, choose the project and use Project research dossier to save questions, approach/methods, findings/conclusions and limitations/missing evidence.

Include papers in Scientific Watch first. In the dossier, choose one of your included papers, write a project-specific rationale and select Add paper to shared dossier. The citation, abstract excerpt, evidence basis and capture time are copied as a snapshot. Private screening annotations are never copied. Later changes to the private review do not silently alter the shared dossier. Duplicate DOI/URL records are rejected. References can be removed and added again with a revised rationale.

Export readable dossier produces standalone HTML with the narrative, source snapshots, project rationales and current milestones, deliverables, risks and outstanding-work warnings. It needs no external assets or AI service. Open the file in a browser to read or print it. It is a working report, not supervisor approval, a frozen archive or a scientific-quality assessment. The existing JSON completion report remains available for the more detailed operational/financial snapshot.

## Access and persistence

- Uses the existing internal MIS access model: authenticated laboratory users can read projects/dossiers; researchers, reviewers and administrators can edit. There is no project-membership ACL. Private or restricted collaborations need that separate access feature before use.
- Literature selection checks ownership of the source review and requires an included paper. Another user's private review cannot be imported by guessing its ID.
- The UI explicitly describes what becomes shared. Account-scoped query keys prevent cached dossiers from being reused across accounts.
- Each mutation increments a revision; conditional updates reject stale saves with HTTP 409 instead of silently overwriting another edit. The editor preserves pending text on an error and offers explicit reload. Save narrative edits before changing references or exporting.
- Revision numbers are conflict protection, not retained revision history. The current editor and update time are stored; earlier narrative versions are not archived.
- Alembic revision `q7f4a1b5c0d2` adds `mis_project_dossiers`. PostgreSQL enables RLS and revokes browser-client grants when those roles exist. Access uses the trusted backend database connection. PostgreSQL/Supabase deployment was not exercised in this pass; [RLS guidance](https://supabase.com/docs/guides/database/postgres/row-level-security) informed the migration.
- GET requests do not create dossier records. Text sizes and a 100-reference limit bound each dossier.

## Verification

26 offline regression tests passed in 23.333 seconds on isolated migrated SQLite databases. New coverage checks missing projects, invalid input, saved narrative, stale revisions, private-review ownership, pending-paper rejection, duplicate selection, snapshot stability after review changes, private-note isolation, removal, viewer write restrictions and HTML escaping of hostile text.

Frontend TypeScript and production build passed. The existing large JavaScript bundle advisory remains.

`python scripts/verify_project_dossier.py` creates a clearly labelled synthetic project and paper in `tmp/integration-evidence/dossier-demo.db`, exercises the API workflow and writes `project-dossier.html` plus `dossier-demo.json`. It does not contact providers or modify the laboratory database. Repeated runs add a fresh demo project to this isolated database.

Browser verification: loaded the synthetic dossier under Research Projects, changed and saved a question, observed the revision change from 2 to 3 and the saved-state indicator, inspected the screen layout and invoked the HTML export. The API export content was checked independently. Opening the generated local HTML file for browser rendering was blocked by the browser's URL policy; exported-file visual/print rendering and the saved browser download were not verified. The generated HTML source and escaping were checked, not its printed pagination.

## Next milestone

Supervisor submission, comments, requests for changes, approval and immutable version snapshots remain separate work. Findings currently use free text; there is no claim-level citation mapping or automatic scientific appraisal. Production database concurrency, full authenticated deployment and mobile/print layout still require verification. None of these implementation checks validate field predictions or scientific conclusions.
