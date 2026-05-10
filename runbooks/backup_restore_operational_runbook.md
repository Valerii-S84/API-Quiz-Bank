# Backup and Restore Operational Runbook

Status: protected beta SQLite protocol executed on the VPS plus
owner-operated protected production PostgreSQL backup/restore protocol.

## Scope

This runbook defines the operational backup/restore protocol for protected beta
execution and the owner-operated protected production PostgreSQL runtime. It
does not approve broad public, school or paid launch backup claims.

## Backup Preconditions

- Pilot environment is named.
- Data store is identified.
- Backup owner is assigned.
- Backup location is access-controlled.
- Retention window is documented.
- Restore target can be isolated from active pilot runtime.

## Backup Procedure

1. Announce backup window or confirm online backup safety.
2. Run approved backup command/mechanism for pilot data store.
3. Record backup id/path, created time, size and checksum if available.
4. Confirm backup job success through logs or provider status.
5. Store evidence in the pilot evidence package.

Required evidence:

- backup id or artifact path;
- timestamp;
- data store identifier;
- size/checksum or provider equivalent;
- owner;
- retention window.

## Restore Drill Procedure

1. Select backup artifact.
2. Restore into isolated target.
3. Confirm no write occurs against active pilot target.
4. Run readiness check against restored target.
5. Run minimal delivery behavior check if safe.
6. Record result and limitations.

Required evidence:

- source backup id;
- restore target;
- readiness result;
- sample query or behavior check;
- operator and reviewer;
- pass/fail decision.

## PostgreSQL Production-Like Profile

Use `database/postgresql/001_create_runtime.sql` for the isolated schema
profile. Production credentials must be supplied outside the repository.

Minimum init command:

```bash
psql "$QUIZBANK_DATABASE_URL" -v ON_ERROR_STOP=1 \
  -f database/postgresql/001_create_runtime.sql
```

Minimum backup command:

```bash
pg_dump --format=custom --file="$BACKUP_PATH" "$QUIZBANK_DATABASE_URL"
```

Minimum isolated restore command:

```bash
createdb "$QUIZBANK_RESTORE_DATABASE"
pg_restore --dbname="$QUIZBANK_RESTORE_DATABASE" --clean --if-exists "$BACKUP_PATH"
```

The restore drill is not closed until readiness and a minimal delivery behavior
check run against the restored database target.

## Protected Production PostgreSQL Backup Command

Use `scripts/api_quiz_bank_postgres_backup.sh` for the owner-operated protected
runtime.

Required environment controls:

| Variable | Purpose |
|---|---|
| `API_QUIZ_BANK_BACKUP_RETENTION_DAYS` | local/offsite cleanup window, default `30` |
| `API_QUIZ_BANK_BACKUP_OFFSITE_DIR` | off-server mounted path or managed-backup export target |
| `API_QUIZ_BANK_BACKUP_ENCRYPTION_KEY_FILE` | optional secret key file for encrypted artifacts |
| `API_QUIZ_BANK_BACKUP_CREATED_BY` | job/operator label in metadata |

The backup command writes:

- PostgreSQL custom dump or encrypted dump;
- `.meta` sidecar with size, checksum, retention, storage and restore status;
- offsite copy when `API_QUIZ_BANK_BACKUP_OFFSITE_DIR` is configured;
- retention cleanup for matching backup artifacts.

## Protected Production Restore Drill Cadence

Use `scripts/api_quiz_bank_postgres_restore_drill.sh` at least every 30 days for
the owner-operated protected production runtime.

Required environment controls:

| Variable | Purpose |
|---|---|
| `API_QUIZ_BANK_POSTGRES_BACKUP_PATH` | selected backup artifact |
| `API_QUIZ_BANK_RESTORE_DRILL_REPORT_DIR` | restore drill report directory |
| `API_QUIZ_BANK_RESTORE_DRILL_INTERVAL_DAYS` | required cadence, default `30` |
| `API_QUIZ_BANK_RESTORE_DRILL_OWNER` | accountable operator |

Each drill must restore into an isolated database, verify required runtime
tables and write a report with owner, source backup, target database, status and
next due interval.

## Protected Production RPO/RTO

| Scope | Target |
|---|---|
| RPO | 24 hours for owner-operated protected production runtime |
| RTO | same business day for owner-operated protected production runtime |
| Restore drill cadence | at least every 30 days |
| Retention | 30 days local/offsite default unless legal/privacy policy narrows it |
| Off-server backup | required by offsite copy or managed provider evidence |
| Encryption | provider encryption or script-level encrypted artifact |

## Failure Handling

- If backup fails, pilot launch is no-go.
- If restore target cannot be isolated, pilot launch is no-go.
- If readiness fails after restore, pilot launch is no-go.
- If backup artifacts expose secrets or personal data beyond approved access,
  open incident/security review.

## Non-Closure Rule

This runbook closes database operations only for the owner-operated protected
production API runtime when the timer, offsite/managed backup evidence,
retention cleanup, encryption policy and periodic restore drill evidence are
recorded. Broader public, school, paid or scale launch still requires separate
managed-provider and legal/privacy review.
