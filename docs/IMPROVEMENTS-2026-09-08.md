# Submission improvement pass — 8 September 2026

This record supersedes the defect status in the 7 September baseline assessment. The project remains an internship MVP; real laboratory data is still to be obtained.

## Completed

| Baseline issue | Implemented change | Verification |
| --- | --- | --- |
| Manual advice bypassed quality review | Shared eligibility for advice, scenarios and schedules; pending, erroneous, rejected, non-field, stale and future readings are blocked | Regression tests exercise rejection paths and the valid approval chain |
| Uploads could be used before validation | All ingestion starts pending; quality reads persisted state and protects completed review decisions from duplicate ingestion events | Pending-ingestion test |
| Only newest CSV row was validated | Every imported row emits a quality request; only newest eligible reading can generate advice; processed records cannot be silently overwritten | Three historical rows plus a malformed row tested |
| Corrections could accept impossible values | Unchanged errors cannot be accepted; corrections are schema-checked and physically assessed; traced advice inputs cannot be rewritten | Invalid and valid correction tests |
| Project dates returned 500 | Validated merge for project/staff/equipment/budget updates, typed dates and forbidden ID/unknown-field changes | Date/status/negative-value regression |
| Project lifecycle missing in UI | Edit form for owner, dates, budget and status; Suspended column; timeline edit entry | Browser creation and edit to Suspended with persisted date and owner |
| Resource setup hidden in Administration | Add budget/equipment/staff directly in project operations; selected project prefilled for budget | Browser budget creation and updated available balance |
| Failed collection appeared successful | RSS, ArXiv and PubMed propagate failures; all-source failure becomes failed; enrichment errors become visible warnings; failed fetch does not advance successful-fetch timestamp | Mocked fetch and embedding failures |
| Invalid parcel parameters accepted | Positive/finite area, coordinate bounds and consistent field-capacity/wilting-point range | Domain-validation regression |
| MIS agent did not subscribe | Project create/update events now request quality checks through MIS | Project quality report observed in regression suite |
| Viewer role fell back to researcher | Viewer added end-to-end; unknown/missing roles become read-only; all authenticated mutation routes reject viewers | Mocked Supabase identities and private-route tests |
| Approval controls ignored roles | Main recommendation/planning/schedule/calibration controls now disable for non-reviewers; shared submit controls and project editing respect read-only access | Type-check; backend permission regressions. Full authenticated browser-role walkthrough remains to do |
| Claims exceeded evidence | Welcome/capability copy narrowed, planned navigation labeled, fake 0% trend badges removed; calibration labeled Fit RMSE | Browser inspection and source review |
| No maintained regression suite or root setup guide | Offline unittest suite, fresh migration exercise, root README, CI definition and field-evaluation protocol added | Local suite and frontend checks; remote CI has not run |

The suite currently contains 13 tests, including a valid forecast-backed simulation and quota-limited schedule with mocked forecast inputs. Temporary test data is explicitly synthetic even where a `field` origin is used to exercise the production branch. No existing lab database was modified. Browser writes use `review-2026-09-08.db`, an isolated local database excluded from version control.

## Verification result

- Backend: 13 regression tests passed in 10.057 seconds; migrations applied to a fresh temporary database.
- Frontend: TypeScript check passed; Vite production build passed (2,318 modules, about 1.095 MB JavaScript / 290 kB gzip). The bundle-size advisory remains.
- Browser: created a project, edited owner and end date, moved it to Suspended, and created a linked budget from the project screen. All writes used the isolated review database.
- Remote CI, live provider calls and real authenticated browser roles were not executed.

## Intentional behavior changes

- Accounts without an explicit `app_metadata.lab_role` are now viewers. An authorized administrator must assign the intended editing/review role through the existing Supabase administration process.
- The newest measurement controls operational eligibility; the default freshness limit is 48 hours and is configurable. Old/demo data can be inspected but does not generate current operational advice.
- CSV is not a way to rewrite a processed measurement. Use a reviewed correction where allowed, or a new observation; old advice provenance is preserved.
- Legacy optimization runs without a source-reading reference must be regenerated before approval.
- Calibration metrics retain the legacy response field for compatibility and add `fit_observations`; the UI describes the metric as in-sample fit.

## Still outstanding

1. Obtain authorized real parcel observations and a researcher/publication example. Agree the measurement timing, units, freshness policy and internship scope with the supervisor. See `FIELD-EVALUATION-PROTOCOL.md`.
2. Execute live provider checks for scholarly sources, Mistral and weather, plus actual Supabase login and role-specific browser walkthroughs. Offline tests do not prove provider availability or scientific accuracy.
3. Validate PostgreSQL/pgvector migrations and a durable broker deployment; test restart/retry behavior, backups and restoration. The local verification uses SQLite and memory transport.
4. Run the new CI on the exact submitted revision and perform a clean installation. Significant pre-existing uncommitted application files and migrations still need inclusion in the submission revision; nothing was pushed or deployed by this improvement pass.
5. Confirm the previously reported historical ScraperAPI credential has been rotated. No key was printed or changed during this pass.
6. Keep remaining website/GIS sections explicitly planned until their scope is agreed. The public catalogue is implemented, while the dedicated internal dataset page remains a placeholder with curation available through Administration.
7. The main React file remains large and the build emits a bundle-size advisory. Page extraction/code splitting and broader accessibility/mobile work are follow-up maintenance, not evidence that the core workflow is complete.

This pass improves the existing operational paths and their testability. It does not establish field validity, implement the entire original cahier, or certify production readiness.
