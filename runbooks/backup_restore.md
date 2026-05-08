# API Quiz Bank Backup and Restore Runbook

Status: MVP-local and Public MVP / Protected Beta SQLite backup/restore
runbook; not a production database backup plan.

## Scope

This runbook covers local and protected-beta SQLite MVP backup/restore proof and
defines what must be replaced or extended before production claims.

## Local SQLite MVP Backup

1. Stop local writes to the MVP database.
2. Identify the DB path, normally `var/quizbank_mvp.sqlite3`.
3. Create an artifact directory:

```bash
mkdir -p var/backups
```

4. Copy the database with a timestamped name:

```bash
cp var/quizbank_mvp.sqlite3 var/backups/quizbank_mvp_YYYYMMDD_HHMMSS.sqlite3
```

5. Record checksum and size:

```bash
python3 - <<'PY'
from pathlib import Path
import hashlib

path = Path("var/backups/quizbank_mvp_YYYYMMDD_HHMMSS.sqlite3")
print(path, path.stat().st_size, hashlib.sha256(path.read_bytes()).hexdigest())
PY
```

## Local SQLite MVP Restore Drill

1. Restore only into a safe target path, not over the active DB:

```bash
cp var/backups/quizbank_mvp_YYYYMMDD_HHMMSS.sqlite3 var/restore_drill.sqlite3
```

2. Verify schema readiness:

```bash
QUIZBANK_DB_PATH=var/restore_drill.sqlite3 PYTHONPATH=src python3 - <<'PY'
from quizbank_mvp.database import database_is_ready

raise SystemExit(0 if database_is_ready() else 1)
PY
```

3. Run the MVP demo against an isolated DB as a behavioral comparison:

```bash
PYTHONPATH=src python3 tools/run_mvp_demo.py
```

4. Record restore result in `reports/restore/` before using this as pilot/prod evidence.

## Public MVP / Protected Beta Evidence

Protected beta backup/restore evidence is recorded in:

- `reports/beta/backup_timer_evidence_2026-05-08.md`;
- `reports/restore/public_mvp_backup_restore_2026-05-08.md`;
- `reports/rollback/public_mvp_runtime_rollback_drill_2026-05-08.md`.

Minimum protected beta closure:

- systemd backup timer active and enabled;
- latest backup command returns `backup-ok`;
- latest restore drill writes to an isolated target and returns
  `restore-drill-ok`;
- restore target is never the active runtime DB;
- backup path is under `/var/backups/api-quiz-bank`.

## Production Requirements

- Managed DB backup mechanism identified.
- Backup metadata recorded.
- Restore target isolated from production.
- Restore drill report committed or attached to the release evidence.
- Access to backup artifacts restricted.
- Rollback/restore owner named.

No production phase may be marked complete from this runbook alone.
