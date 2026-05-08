# Server Evidence for Roadmap Sections 17-20

Date: 2026-05-08

Scope: server-side execution evidence for `docs/14_roadmap.md` sections 17-20.
Commands were executed on `root@valerchik.de` against `/opt/api-quiz-bank`.
Secret values were read only on the server and were not printed.

## Server Snapshot

```text
HOST=ubuntu-8gb-nbg1-1
PWD=/opt/api-quiz-bank
BRANCH=main
HEAD=78c899ddb996c64c1ee67f4d9feb29eea55f27da
ORIGIN_MAIN=78c899ddb996c64c1ee67f4d9feb29eea55f27da
TRACKED_DIRTY_COUNT=0
SERVER_ONLY_UNTRACKED=2
CONTAINER=/api-quiz-bank-pilot running/healthy restart=0 started=2026-05-08T15:44:40.275495572Z
IMAGE=sha256:b8df89fa3250b8d87171d6521bb894dd409832e6c66657a0f3731b5b69602831
PORT=127.0.0.1:8010
LOCAL_HEALTH={"status":"ok","service":"api-quiz-bank","version":"0.1.0"}
LOCAL_READY={"status":"ok","checks":[{"name":"database","status":"ok"}]}
BACKUP_TIMER=active
NEXT_BACKUP_TIMER=Sat 2026-05-09 03:20:00 UTC
```

Server worktree status at the time of evidence:

```text
?? docker-compose.api-quiz-bank.secrets.yml
?? docker-compose.api-quiz-bank.yml.bak_20260508T084341Z
```

Tracked runtime changes were reconciled before deploy:

```text
git fetch origin main
git stash push -- docker-compose.api-quiz-bank.yml scripts/api_quiz_bank_backup.sh scripts/api_quiz_bank_restore_drill.sh scripts/api_quiz_bank_smoke.sh
git pull --ff-only origin main
docker compose -f docker-compose.api-quiz-bank.yml up --build -d
```

The untracked files listed above are server-only runtime/override artifacts and
were not printed, committed or copied into this repository.

## Backup And Restore Evidence

Executed on the server:

```text
QUIZBANK_DB_PATH=var/api-quiz-bank/quizbank_mvp.sqlite3 \
  API_QUIZ_BANK_BACKUP_DIR=/var/backups/api-quiz-bank \
  sh scripts/api_quiz_bank_backup.sh
-> backup-ok /var/backups/api-quiz-bank/quizbank_mvp_20260508T154554Z.sqlite3

QUIZBANK_DB_PATH=var/api-quiz-bank/quizbank_mvp.sqlite3 \
  API_QUIZ_BANK_RESTORE_DRILL_DIR=/var/backups/api-quiz-bank/restore-drills/20260508T154554Z_roadmap_11_14 \
  sh scripts/api_quiz_bank_restore_drill.sh
-> restore-drill-ok /var/backups/api-quiz-bank/restore-drills/20260508T154554Z_roadmap_11_14/restore_drill.sqlite3
```

Executable-bit note: after the clean checkout, `./scripts/api_quiz_bank_smoke.sh`
returned `Permission denied` because the committed script mode is non-executable.
The operational smoke was rerun as `sh scripts/api_quiz_bank_smoke.sh` and
returned `smoke-ok`.

Repository remediation after this evidence run:

```text
scripts/api_quiz_bank_backup.sh -> Git mode 100755
scripts/api_quiz_bank_restore_drill.sh -> Git mode 100755
scripts/api_quiz_bank_smoke.sh -> Git mode 100755
```

The remediation is recorded in the local repository state. The already-running
VPS was not redeployed again for this file-mode-only change.

## Protected Public Route Smoke

Evidence consumers and API credentials were created through the deployed runtime
CLI and direct Python helper functions. Secret values were generated/read only
on the server and were not printed.

Result:

```json
{
  "delivery_read": {
    "delivery_status": "created",
    "status": 200
  },
  "entitlement": {
    "reason_code": "ENTITLEMENT_MISSING_FEATURE",
    "status": 403
  },
  "health": 200,
  "missing_app": {
    "reason_code": "AUTH_REQUIRED",
    "status": 401
  },
  "next_item": {
    "answer_key_leaked": false,
    "delivery_created": true,
    "explanation_leaked": false,
    "reason_code": null,
    "status": 200
  },
  "no_edge": 401,
  "quota": {
    "reason_code": "QUOTA_EXCEEDED",
    "status": 429
  },
  "ready": 200,
  "repeat": {
    "reason_code": "SELECTION_NO_ELIGIBLE_ITEM",
    "status": 404
  },
  "suspended": {
    "reason_code": "CONSUMER_NOT_ACTIVE",
    "status": 403
  }
}
```

## Server Disable / Rollback-Control Evidence

An evidence consumer was created, suspended with the server CLI, and then tested
through the protected public route.

```json
{
  "suspended_delivery": {
    "reason_code": "CONSUMER_NOT_ACTIVE",
    "status": 403
  }
}
```

Database verification:

```json
{
  "delivery_count_after_suspend": 0,
  "latest_audit": {
    "action": "consumer_status_transition",
    "from_status": "active",
    "to_status": "suspended"
  }
}
```

## Server PostgreSQL Contract Smoke

An isolated PostgreSQL container was started on the server from a temporary
copy of the committed PostgreSQL schema and control import artifacts. This did
not modify the live API runtime.

```json
{
  "checks": {
    "counts": {
      "import_batch_items": 2,
      "import_batches": 1,
      "import_validation_results": 0,
      "quiz_items": 2,
      "sources": 1
    },
    "lineage_join_count": 2,
    "load_plan_applied": true,
    "schema_applied": true,
    "source_checksum_match": true
  },
  "database": "postgres",
  "docker_image": "postgres:16-alpine",
  "executed_at": "2026-05-08T15:48:00Z",
  "report_type": "postgresql_contract_smoke"
}
```

## Production Target Decision

Decision:

```text
The current VPS is cleanly deployed as the protected API runtime, but it is not
promoted to the production target by this evidence pass.
```

Reason:

- the active data store is still SQLite, not a persistent production database;
- backup timer and restore drill exist, but no external production monitoring
  or alert source is recorded;
- no production legal/privacy launch approval is recorded;
- no full deployment rollback execution is recorded.

## Closure Impact

| Roadmap section | Server evidence result |
|---|---|
| 17 Phase 7 Closed Pilot Hardening | Server evidence remains closed. |
| 18 Phase 8 Public Beta Readiness | Server-side operational evidence is closed for protected beta smoke; broader beta remains gated. |
| 19 Phase 9 Production Readiness | Clean protected deploy exists; production remains NO-GO. |
| 20 MVP Cut | Server evidence confirms MVP-local runtime behavior through protected route. |

## Remaining Production Boundary

Production readiness still requires production target approval, a persistent
production database decision, monitored production backup evidence, production
dashboard or alert source, full deployment rollback execution and legal/privacy
launch approval.
