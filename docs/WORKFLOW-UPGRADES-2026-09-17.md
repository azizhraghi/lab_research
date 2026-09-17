# Six workflow upgrades — 17 September 2026

This release improves all six existing workflows. It does not complete every original laboratory requirement or establish scientific validity.

| Workflow | New behavior | Remaining boundary |
|---|---|---|
| Project management | Resumable setup guide checks team, budget, milestone and deliverable records. Assign available staff with a conditional update that rejects conflicting assignments. Budget history shows entries and the difference from the spent total; expense increments are atomic. | One current project per staff member. Each setup step saves separately. No commitment settlement/reversal or complete accounting reconciliation. |
| Literature to evidence | Share included papers directly from Scientific Watch into a chosen project with an explicit rationale. Dossiers show captured excerpts and citation counts; exported finding links identify deliverables and evaluations by name. | Private screening notes are not copied. Excerpts are not full-text appraisal. Revision checks reject concurrent edits and duplicate references. |
| Researcher to CV | Publication checks inside the identity panel flag missing metadata and repeated normalized titles, with DOI links and refresh after sync. | Missing DOI is not automatically an error; repeated titles are inspection candidates. Authorship and citation counts remain unverified. CV delivery is unchanged from the earlier release. |
| Parcel to application | IoT Monitoring shows measurement origin/review, current operational eligibility, advice source, approval and linked application amounts. Manual refresh and 15-second polling. | Latest 100 records per category. Logged applications do not establish water savings. Demo data cannot authorize advice. Paired evaluation remains in the project dossier, not automatically derived from the trail. |
| Supervisor review | Compare two preserved submissions, including narrative, evidence and operational changes. Exports distinguish submissions from working drafts. | Laboratory-wide internal access. Generation timestamps are excluded from comparisons. No signed change record; approval applies to one version. |
| Deployment | Read-only preflight explicitly reports missing Docker. Operations commands save JSON evidence without overwriting reports. Broker recovery requires the exact project event to be delivered and processed by the orchestrator; CI retains reports. | Docker unavailable here. Container builds, PostgreSQL restoration and real broker recovery remain unexecuted locally. No remote CI result or production deployment claimed. |

## Demonstration

1. Choose a project under Laboratory operations. Follow the setup guide; completed steps come from saved records.
2. Inspect Budget entry history and explain any difference from the spent total.
3. In Scientific Watch, include and save a paper, expand **Use this included paper in a project**, select the project and enter its relevance. Inspect the captured evidence in the dossier and connect it to a finding.
4. In Researchers, expand identity review and publication checks. Inspect provider records before asserting authorship or exporting a CV.
5. In IoT Monitoring, inspect **Measurement → advice → application**. Synthetic or unreviewed measurements remain blocked from operational advice.
6. Expand **Compare submitted versions** in a dossier with two submissions. The browser example compares revisions 5 and 6 and identifies an added proposed finding.

```sh
python scripts/manage_demo.py preflight --report artifacts/preflight.json
python scripts/manage_demo.py check --report artifacts/health.json
python scripts/manage_demo.py fault-check --report artifacts/recovery.json
python scripts/manage_demo.py restore-check --file backups/demo.dump --report artifacts/restore.json
```

Use new report paths for each run. Fault-check stops Redis in the isolated Compose demo; do not run it during real laboratory operations. Blocked preflight exits nonzero.

## Verification boundaries

Final local checks: 35 offline tests passed in 21.574 seconds. TypeScript checking and the production frontend build passed (16.97 seconds, 2,331 modules). The existing large JavaScript bundle advisory remains (approximately 1.15 MB before compression). Deployment preflight recorded Docker unavailable, rather than a passing runtime result.

The regression suite covers assignment conflicts and role checks, parcel isolation and demo gating, publication warnings, evidence changes and submission comparison. Earlier tests cover review independence, snapshot preservation, source privacy, budget totals, quality gates and SQLite backup/restore.

Desktop browser checks confirmed setup progress and the added finding between revisions 5 and 6. Sharing, publication-audit and parcel-trail screens have not received complete browser interaction coverage. Export print layout, authenticated multi-account use, Docker deployment and field science remain unverified.

No new migration in this increment. Apply the existing Alembic head when updating an older checkout. Changes remain uncommitted; include all intended source files in the eventual handover revision, excluding local databases and logs.
