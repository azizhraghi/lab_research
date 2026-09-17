# Project workflow improvement — 12 September 2026

## Delivered

The project screen now includes a completion checklist and status controls for
all recorded milestones, deliverables and risks. Deliverables can move through
planned, draft, submitted and approved; approval requires a reviewer or
administrator and prior submission. Editing an approved deliverable returns it
to draft and clears its submission timestamp. Required fields cannot be nulled
through partial updates; operational update schemas reject unknown fields.

New deliverables accept an optional due date instead of silently assigning today.
New staff created from project operations is linked to that project. Multiple
project budgets can be selected before recording activity. Mutation errors are
shown, and viewer controls are disabled. Milestone, risk and deliverable lists
no longer silently stop after five records.

`GET /api/mis/projets/{project_id}/completion-report` returns an authenticated
project-wide snapshot with project metadata, all milestones and deliverables
(including undated records), risks, assigned staff, individual budget balances,
financial entries and outstanding-work warnings. Currency amounts remain separate
per budget. The screen shows the report and provides a JSON download button that
refetches current data before export.

## Walkthrough

1. Create a project and set its lead and dates. Move it to Active when appropriate.
2. Add staff and budgets from Laboratory operations; equipment registration and
   reservation use the existing resource controls.
3. Record milestones, deliverables, risks and financial activity.
4. In Project completion & report, complete milestones, submit deliverables,
   approve them as reviewer/administrator, and resolve risks.
5. Review outstanding-work warnings and budget balances. Use Edit project to
   set Completed when the project lead decides it is complete.
6. Download the current JSON report for the handover record.

## Verification

- 19 offline backend tests passed in 16.479 seconds. The new lifecycle regression
  covers planned → active → completed, assigned staff, a recorded expense and its
  report balance, incomplete-work warnings, milestone completion, submission,
  rejection of premature approval, researcher approval denial, reviewer/admin
  approval, risk mitigation and return to draft after editing approved content.
- TypeScript and production build passed; the existing bundle advisory remains
  (approximately 1.105 MB JavaScript before compression).
- Browser on isolated `review-project-2026-09-12.db`: completed a milestone,
  submitted and approved a deliverable, closed a risk and observed the checklist
  update to no outstanding recorded work. Inspected the rendered checklist.
- The browser download button was exercised; its saved file was not inspected.
  Report payload and financial values were verified by the API regression.
- Existing laboratory databases were untouched. No production deployment or
  new schema migration was needed for these changes.

## Limits and next work

The completion report is a current operational snapshot, not an immutable signed
closure. Project status changes remain an editor decision; outstanding work is
reported rather than enforced as a new administrative policy. Completed projects
can still be edited, and subsequent unfinished work is visible in the report.

The existing commitment model sums recorded commitments; commitment settlement,
expense reversal and accounting reconciliation remain unfinished. The report
is not an accounting statement. Equipment reservations, maintenance and workload
retain their existing workflows and were not comprehensively revalidated here.
Staff assignment still represents one current project, not a multi-project
allocation model. Report rendering to PDF and archived signed reports remain
future work.
