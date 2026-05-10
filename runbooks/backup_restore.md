# API Quiz Bank Backup and Restore Runbook

Status: MVP-local, Public MVP / Protected Beta SQLite and owner-operated
protected production PostgreSQL backup/restore runbook.

## Scope

This runbook covers local and protected-beta SQLite MVP backup/restore proof
plus the owner-operated protected production PostgreSQL runtime. The production
scope is limited to the protected API runtime and does not approve broad public,
school or paid launch.

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

## Protected Production PostgreSQL Operations

The protected production PostgreSQL backup command is
`scripts/api_quiz_bank_postgres_backup.sh`.

Required controls:

- daily systemd timer or equivalent scheduled execution;
- backup metadata sidecar for each artifact;
- backup retention cleanup using `API_QUIZ_BANK_BACKUP_RETENTION_DAYS`;
- off-server copy or managed backup target using
  `API_QUIZ_BANK_BACKUP_OFFSITE_DIR` or provider equivalent;
- optional encrypted artifact using
  `API_QUIZ_BANK_BACKUP_ENCRYPTION_KEY_FILE`;
- restore drill against an isolated database using
  `scripts/api_quiz_bank_postgres_restore_drill.sh`;
- restore drill report under `API_QUIZ_BANK_RESTORE_DRILL_REPORT_DIR`;
- backup failure and restore failure visible through the production monitor or
  provider timer alerting.

Minimum metadata fields:

```text
backup_id
environment
database_name
created_at_utc
backup_type
backup_format
size_bytes
checksum_sha256
retention_days
created_by
storage_location
offsite_status
restore_tested_status
```

## Protected Production RPO/RTO

For the owner-operated protected production API runtime:

| Target | Value | Evidence requirement |
|---|---:|---|
| RPO | 24 hours | daily PostgreSQL backup timer or managed backup status |
| RTO | same business day | isolated restore drill report and operator runbook |
| Restore drill cadence | at least every 30 days | restore drill report or provider drill evidence |
| Local retention | 30 days by default | `API_QUIZ_BANK_BACKUP_RETENTION_DAYS` |
| Off-server copy | required for production claim | offsite copy status or managed provider backup evidence |

## Encryption Policy

Production backup artifacts must either:

- be encrypted by the storage provider with access restricted to the owner; or
- be encrypted by `scripts/api_quiz_bank_postgres_backup.sh` using
  `API_QUIZ_BANK_BACKUP_ENCRYPTION_KEY_FILE`.

The encryption key file is a secret. It must not be committed, printed in logs
or copied into reports. If the script-level encryption key file is configured,
the plaintext dump is removed after the encrypted artifact is created.

## Production Requirements

- Managed DB backup mechanism identified.
- Backup metadata recorded.
- Restore target isolated from production.
- Restore drill report committed or attached to the release evidence.
- Access to backup artifacts restricted.
- Rollback/restore owner named.

No broad public, school or paid launch may be marked complete from this runbook
alone.
