# API Quiz Bank Backup and Restore Runbook

Status: MVP-local runbook and future pilot/prod gate placeholder.

## Scope

This runbook covers local SQLite MVP backup/restore proof and defines what must be replaced
or extended before pilot, beta or production claims.

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

## Pilot/Beta/Production Requirements

- Managed DB backup mechanism identified.
- Backup metadata recorded.
- Restore target isolated from production.
- Restore drill report committed or attached to the release evidence.
- Access to backup artifacts restricted.
- Rollback/restore owner named.

No pilot, beta or production phase may be marked complete from this runbook alone.
