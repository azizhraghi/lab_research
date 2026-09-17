# Institutional publishing — 11 September 2026

## Delivered

News, events and theses now have administrator screens and a published-only
public catalogue. Open the corresponding sidebar section to create a draft,
edit it, publish it or withdraw it. Other laboratory roles can read published
records but cannot access content administration or mutate these records.

Events require a start date and venue, with an optional end date and information
link. Theses require an author, supervisor and degree (Masters or PhD), with an
optional defence date and repository link. All records require a title and body.
Links are restricted to HTTP(S). Content renders as plain text, not executable HTML.

Saving an edited record returns it to draft, clears publication metadata and
removes it from public display. Publishing is a separate administrator action.
Withdrawal retains the record for editing or republication. The public response
omits the administrator identity. The frontend updates its public cache immediately
when an item is edited or withdrawn, avoiding a stale-content flash on return.

## Database and operation

Run `alembic upgrade head` before starting the updated application. Revision
`o5d2e9f3a8b0` adds `institutional_content`; the existing model import registers it
with application and migration metadata. No existing laboratory database was
migrated during this verification.

On PostgreSQL the migration enables RLS with no client policies: direct browser
Data API access is not the supported path. FastAPI uses a trusted owner/backend
connection and enforces publication and role restrictions. Deployment with a
restricted database role needs explicit backend access configuration and testing.
No remote Supabase or PostgreSQL deployment was performed.

## Evidence

- 18 backend regression tests passed, including all three content kinds through
  draft, publication, edit-to-draft and withdrawal; role denial, anonymous access,
  missing authentication configuration, invalid dates, missing thesis fields,
  blank titles, unsafe URLs and forbidden status injection.
- Tests apply migrations to a fresh temporary SQLite database.
- Browser: created synthetic news, published it, saw it in the public portal,
  edited it back to draft, republished and withdrew it. Rechecked that the public
  view immediately excludes the withdrawn record after the cache fix.
- Event form inspected in the browser for fields and layout.
- Browser writes only used `review-content-2026-09-09.db`, an ignored isolated
  database. The synthetic announcement was left withdrawn.
- TypeScript and production build verified; the existing large-bundle advisory remains.

## Remaining scope

These are institutional publishing workflows, not event registration or internal
thesis-progress management. No claims of attendance, actual theses, defence
schedules or institutional approval were invented. Approved content is still
needed before a public launch. File uploads, calendar export, search/pagination,
revision history and concurrent-editor conflict handling are future enhancements.
