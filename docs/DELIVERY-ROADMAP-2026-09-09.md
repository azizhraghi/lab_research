# Next delivery milestones

Missing laboratory measurements block field validation, not product development.
The target is a complete, demonstrable internship workbench with explicit evidence
for each capability. The following milestones are not claims of completed work.

| Priority | Deliverable | Completion evidence | Needs lab measurements? |
| --- | --- | --- | --- |
| 1 | Reliable agent delivery | Fault-injection tests for interrupted delivery, retry exhaustion and recovery; then real Redis restart exercise | No |
| 2 | Institutional content workflows | Administrator can draft, publish and withdraw news, events and theses; anonymous visitors see published content only | No; approved institutional content needed for publication |
| 3 | Complete project walkthrough | Create a project, assign resources, manage milestones and deliverables, record expenditure, finish and report; verify role restrictions | No |
| 4 | Scientific watch and bibliography demonstration | Public-source collection and identifier-based publication example, traceable sources, visible provider errors and downloadable CV | No; provider access and reviewed identity needed |
| 5 | Reproducible application package | Fresh installation, application plus database/broker startup, readiness, backup and restore, CI on submitted revision | No |
| 6 | Scientific evaluation | Independent held-out measurements, baseline comparison, documented errors and domain review | Yes |

Synthetic fixtures can demonstrate behavior and test invariants. They must remain
isolated from operational records and cannot substantiate predictive accuracy,
water savings, or laboratory endorsement. GIS and external scientific engines
remain separate scope decisions with concrete use cases before implementation.

## Delivery recovery improvement

Previously the dispatcher recovered expired claims only at startup. If a process
restarted while an earlier claim was still valid, that claim could expire later
and remain stuck indefinitely. Recovery now runs on every polling cycle while
preserving unexpired claims.

Three new tests use an isolated SQLite database and an injected publisher:

- A claim valid at restart expires and is delivered by a subsequent poll.
- A broker failure leaves the event persisted and a replacement dispatcher delivers it.
- Retry exhaustion remains visible until explicit retry, then delivery succeeds.

This is application-level fault injection. A real Redis/Kafka outage, multiple
workers and PostgreSQL behavior still require deployment testing. Delivery is
at least once; successful transport acknowledgement is not evidence that every
downstream agent has completed its work.

## 11 September update

The institutional publishing milestone now has implementation and local verification; see `INSTITUTIONAL-PUBLISHING-2026-09-11.md`. Remaining event registration and thesis-progress features are not included in that milestone.

## 12 September update

Project operations gained deliverable approval, risk-resolution controls, staff linkage, multi-budget selection and project-wide completion reporting. See `PROJECT-WORKFLOW-2026-09-12.md` for evidence and remaining closure/accounting limitations.

Topic review milestone (12 September): live PubMed abstracts, private inclusion/exclusion notes and annotated text bibliography export implemented. 24 regression tests and production build pass; three live abstracts and one export verified in isolation. See LITERATURE-REVIEW-2026-09-12.md. Full-text appraisal, team review, researcher identity confirmation and citation metric validation remain separate work.

16 September: project research dossiers implemented with private-review ownership checks, explicit shared citation snapshots, conflict detection and readable HTML export. 26 regression tests, TypeScript and production build pass. Next: supervisor review with immutable submissions, then reproducible deployment and backup/recovery verification. See PROJECT-DOSSIER-2026-09-16.md.

17 September: connected research release implemented: findings/evidence, evaluations, preserved submissions, independent decisions, attention dashboard, bibliographic trust and provider provenance, delivery history, local backup tools and a full localhost Compose package. 30 offline tests pass. Browser verified a new submission while preserving earlier approval and dashboard attention. Docker-dependent package/recovery checks remain blocked by missing Docker; real scientific validation remains blocked by missing lab measurements. See SUPERVISOR-HANDOVER-2026-09-16.md.
