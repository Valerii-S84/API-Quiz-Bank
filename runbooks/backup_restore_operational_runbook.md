# Backup and Restore Operational Runbook

Status: future pilot operational protocol; not executed on a server.

## Scope

This runbook defines the operational backup/restore protocol needed for future
pilot execution. It extends local MVP notes but does not prove managed pilot
backup readiness.

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

Use `database/postgresql/001_create_runtime.sql` for the isolated
production-like schema profile. The target must be a non-production PostgreSQL
database with credentials supplied outside the repository.

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

## Failure Handling

- If backup fails, pilot launch is no-go.
- If restore target cannot be isolated, pilot launch is no-go.
- If readiness fails after restore, pilot launch is no-go.
- If backup artifacts expose secrets or personal data beyond approved access,
  open incident/security review.

## Non-Closure Rule

Local SQLite restore evidence is useful pre-pilot evidence, but it does not
close pilot backup/restore readiness for a managed environment.
