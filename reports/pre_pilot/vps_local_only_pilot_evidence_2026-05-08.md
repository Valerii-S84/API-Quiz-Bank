# VPS Local-Only Pilot Evidence

Date: 2026-05-08

Status: local-only VPS pilot evidence recorded; not public beta or production.

## Scope

This report records the closed pilot evidence gathered from the existing VPS
checkout and Docker runtime before the later protected public-route slice. It
does not approve public beta, production, Telegram real send, Quiz Arena product
changes or IT Bot changes.

## Environment Gate

| Field | Evidence |
|---|---|
| Environment id | `local-only-vps` |
| Owner | project owner / authorized VPS operator |
| Repository path | `/opt/api-quiz-bank` |
| Active data path observed | `/opt/api-quiz-bank/var/api-quiz-bank/quizbank_mvp.sqlite3` |
| Backup path | `/var/backups/api-quiz-bank` |
| Restore drill path | `/var/backups/api-quiz-bank/restore-drills/20260508T081434Z/restore_drill.sqlite3` |
| Access boundary at time of this slice | SSH operator access only; API bound to `127.0.0.1:8010`; no public route yet |
| Container | `api-quiz-bank-pilot` |

## Checkout Sync Evidence

Command scope: `git fetch origin main`, `git checkout main`,
`git pull --ff-only origin main` inside `/opt/api-quiz-bank`.

No `docker compose up`, restart, Caddy change or bot command was executed in
this checkout-only slice.

| Check | Result |
|---|---|
| Branch before sync | `main` |
| HEAD before sync | `61e32d7362203d9b765d5fe89a09930f585f3758` |
| HEAD after sync | `a86d6251148adbb574067ca68d429a531c0f8380` |
| `origin/main` after sync | `a86d6251148adbb574067ca68d429a531c0f8380` |
| Sync mode | fast-forward |

## Runtime Stability Evidence

| Check | Before | After | Final |
|---|---|---|---|
| Container state | `running/healthy` | `running/healthy` | `running/healthy` |
| Started at | `2026-05-08T07:46:48.873758412Z` | `2026-05-08T07:46:48.873758412Z` | `2026-05-08T07:46:48.873758412Z` |
| Restart count | `0` | `0` | `0` |
| Port bind | `127.0.0.1:8010` | `127.0.0.1:8010` | `127.0.0.1:8010` |

Conclusion: checkout changed, runtime process did not restart.

## Server-Side Smoke Evidence

Executed on the VPS after checkout sync:

```text
curl http://127.0.0.1:8010/health
-> {"status":"ok","service":"api-quiz-bank","version":"0.1.0"}

curl http://127.0.0.1:8010/ready
-> {"status":"ok","checks":[{"name":"database","status":"ok"}]}

API_QUIZ_BANK_BASE_URL=http://127.0.0.1:8010 ./scripts/api_quiz_bank_smoke.sh
-> smoke-ok

QUIZBANK_DB_PATH=var/api-quiz-bank/quizbank_mvp.sqlite3 \
  API_QUIZ_BANK_BACKUP_DIR=/var/backups/api-quiz-bank \
  ./scripts/api_quiz_bank_backup.sh
-> backup-ok /var/backups/api-quiz-bank/quizbank_mvp_20260508T081434Z.sqlite3

QUIZBANK_DB_PATH=var/api-quiz-bank/quizbank_mvp.sqlite3 \
  API_QUIZ_BANK_RESTORE_DRILL_DIR=/var/backups/api-quiz-bank/restore-drills/20260508T081434Z \
  ./scripts/api_quiz_bank_restore_drill.sh
-> restore-drill-ok /var/backups/api-quiz-bank/restore-drills/20260508T081434Z/restore_drill.sqlite3
```

## Server-Side Lifecycle and Delivery Evidence

Executed on the VPS through the live loopback API and the active local-only
SQLite DB. Separate evidence consumers were created for this run.

```text
backup-ok /var/backups/api-quiz-bank/quizbank_mvp_20260508T082156Z.sqlite3
seeded quiz items: 1
seeded consumer: consumer_vps_lifecycle_20260508T082156Z
seeded consumer: consumer_vps_quota_20260508T082156Z
```

Result:

```json
{
  "environment": "local-only-vps",
  "base_url": "http://127.0.0.1:8010",
  "consumer_ids": {
    "lifecycle": "consumer_vps_lifecycle_20260508T082156Z",
    "quota": "consumer_vps_quota_20260508T082156Z"
  },
  "results": {
    "initial_delivery": {
      "status_code": 200,
      "delivery_created": true,
      "reason_code": null
    },
    "suspended_denial": {
      "status_code": 403,
      "reason_code": "CONSUMER_NOT_ACTIVE"
    },
    "blocked_denial": {
      "status_code": 403,
      "reason_code": "CONSUMER_NOT_ACTIVE"
    },
    "reactivated_repeat_guard": {
      "status_code": 404,
      "delivery_created": false,
      "reason_code": "SELECTION_NO_ELIGIBLE_ITEM"
    },
    "repeat_guard": {
      "status_code": 404,
      "delivery_created": false,
      "reason_code": "SELECTION_NO_ELIGIBLE_ITEM"
    },
    "quota_denial": {
      "status_code": 429,
      "reason_code": "QUOTA_EXCEEDED"
    }
  }
}
```

Post-run restore drill:

```text
restore-drill-ok /var/backups/api-quiz-bank/restore-drills/20260508T082156Z_post_lifecycle/restore_drill.sqlite3
```

## Pilot Ops Evidence Pack

| Area | Current pilot evidence |
|---|---|
| Backup owner | project owner / authorized VPS operator |
| Backup cadence | manual backup before/after pilot-affecting operational changes; daily owner-reviewed backup during an active closed-pilot window |
| Retention | keep 7-14 daily closed-pilot backups, plus pre-change backups, under `/var/backups/api-quiz-bank` |
| Restore evidence | VPS restore drill passed against isolated copy at `20260508T081434Z` |
| Lifecycle evidence | active consumer delivery, suspended denial, blocked denial and reactivated repeat guard passed through live loopback API |
| Delivery controls | delivery creation, repeat guard and quota denial passed through live loopback API |
| Telegram dry-run | adapter payload dry-run passed through live loopback API with redacted target and no Telegram Bot API call |
| Runtime disable path | suspend or block a consumer with `PYTHONPATH=src python3 -m quizbank_mvp.cli --db-path var/api-quiz-bank/quizbank_mvp.sqlite3 transition-consumer-status --consumer-id <consumer_id> --to-status suspended --reason <reason>` |
| Deployment rollback path | approved checkout rollback plus rebuild/restart only in a separate rollback execution window; not executed in this evidence slice |
| Monitoring/review cadence | local-only closed pilot requires daily owner review of `/health`, `/ready`, smoke result, backup result, restore-drill status and delivery denials |

## Explicit Non-Evidence

- Public API access and Caddy were not changed in this checkout-only slice.
  A later protected-route slice is recorded separately in
  `reports/pre_pilot/public_api_key_route_evidence_2026-05-08.md`.
- Telegram dry-run was executed without real send; Telegram real send was not executed or approved.
- Quiz Arena and IT Bot paths were not touched.
- This does not prove public beta or production readiness.
