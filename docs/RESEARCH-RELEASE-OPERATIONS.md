# Research release: installation and verification

## Local packaged demonstration

Requirements: Docker with Compose v2, internet access for image/dependency downloads, and Python 3 for the operations script. This package is deliberately a localhost demonstration: authentication is bypassed, credentials are demo-only and the web port binds to `127.0.0.1`. Do not expose it as a production deployment.

```sh
python scripts/manage_demo.py preflight --report artifacts/preflight.json
docker compose -f compose.demo.yml up --build -d --wait --wait-timeout 240
python scripts/manage_demo.py check
```

Open `http://127.0.0.1:8080`. The package includes the frontend, API, pgvector-enabled PostgreSQL and Redis. Database and broker ports are not published. Migrations run before the single API worker starts. Health checks gate startup using Compose's [dependency conditions](https://docs.docker.com/compose/how-tos/startup-order/). Dependencies retain existing version locks; base image tags should be pinned to reviewed digests for a controlled production release.

```sh
python scripts/manage_demo.py backup --file backups/demo-001.dump
python scripts/manage_demo.py restore-check --file backups/demo-001.dump
python scripts/manage_demo.py fault-check
docker compose -f compose.demo.yml down
```

Backup refuses an existing output file. Restore-check creates a new `restore_check_*` database inside the isolated demo PostgreSQL service and checks its migration and project count; it never overwrites `laboratory`. It leaves the restored database for inspection. Check the reported records, not just command success. Fault-check briefly stops the demo Redis service, creates a labelled recovery-test project and checks transport delivery after Redis returns. Run it only on this isolated demo, not during a real lab session. `down` preserves volumes; avoid `down -v` unless deliberately discarding the entire demonstration.

Docker is not installed on the development machine used for this change. YAML parsing and local Python compilation were checked; image builds, Linux dependency installation, PostgreSQL migrations, dump/restore and the real Redis restart still require execution. `.github/workflows/package-demo.yml` runs those checks on an Ubuntu runner, but no remote CI result is claimed. The existing Windows workflow runs offline regression tests and frontend checks.

## Existing Python/Node development setup

Apply `python -m alembic upgrade head` before starting this revision. The new heads add findings/evaluations, submission records and bibliographic provenance. Use the existing environment examples and operator guide for API/frontend startup. No laboratory database was migrated during implementation verification.

```sh
python -m unittest discover -s tests -v
npm --prefix frontend run typecheck
npm --prefix frontend run build
python scripts/verify_project_dossier.py
```

The last command writes only `tmp/integration-evidence/dossier-demo.db` and demonstration reports. It overrides database/provider/auth environment settings locally, uses synthetic papers and account fixtures, and does not call live providers. Repeated runs add a new demo project. To inspect the demo in the UI, run the API with that SQLite file, `ENVIRONMENT=test`, `EVENT_BUS_TYPE=memory`, `DISABLE_AUTH=true`, `CREATE_SCHEMA_ON_STARTUP=false`, `VEILLE_SCHEDULER_ENABLED=false` and empty provider credentials. Point the frontend at that API; keep this setup local.

## Local SQLite backup

```sh
python scripts/backup_sqlite.py path/to/local.db backups/local-snapshot.db
python scripts/backup_sqlite.py backups/local-snapshot.db backups/restored-check.db
```

Uses SQLite's consistent backup API and integrity check, reports table counts and never overwrites the destination. The automated test confirms Unicode content survives backup/restore and overwrite protection works. This is evidence for local SQLite recovery only, not PostgreSQL or broker recovery.

## Before production use

Supply a production deployment with authenticated frontend/API, exact origins, TLS, managed secrets and private database/broker networking. Keep `DISABLE_AUTH=false`. Verify migrations/RLS with the actual backend role; run independent reviewer-account checks; execute backup restore and broker outage checks against an isolated staging environment. Define retention and monitor storage growth: submissions retain complete snapshots and evaluations retain supplied paired rows. Authenticated MIS access remains laboratory-wide. No production deployment or external publication was performed in this work.

Workflow upgrade (17 September): preflight now records missing runtime prerequisites; --report writes a new JSON evidence file. Fault-check now requires orchestrator processing of the recovered project's exact event in addition to transport delivery. CI retains these reports. Docker remains unavailable locally. See WORKFLOW-UPGRADES-2026-09-17.md.
