# Protected Production Corpus Deploy Evidence

Date: 2026-05-11.

Scope: protected VPS PostgreSQL runtime corpus deployment proof for the promoted
QuizBank corpus. This evidence does not approve broad public launch, unauthenticated
API access, school deployment, paid launch or legal/privacy scope expansion.

## Source And Runtime

| Check | Result |
|---|---|
| Promotion evidence commit | `bbe29ec chore(corpus): preserve production promotion evidence` |
| Runtime deploy commit | `510e6554344e28b7fa7691df20478abd90a95143` |
| Runtime commit relation | newer fast-forward commit on `codex/production-readiness-gates` |
| Docker image | `sha256:14a8d2f2a3baf68e49542049b09fe5a2d80abf78351649141c3fae4ac7dd64b1` |
| API container | `running/healthy` |
| PostgreSQL container | `running/healthy` |
| VPS repo status | detached at deploy commit; server-only untracked secrets/private files remain outside Git |

The newer deploy commit clears the current Chainguard Python base image entrypoint
so the existing shell `CMD` starts correctly. The protected runtime was restored
to healthy state before corpus import continued.

## Private Corpus Transfer

| Check | Result |
|---|---|
| Transfer path | `/opt/api-quiz-bank/private/corpus/2026-05-11` |
| Transfer channel | operator-controlled SSH/SCP outside Git |
| Archive SHA-256 | `ccb60957bdf28adb4a6e44b0ca810450b2459f0f4f97e95f7d743d48f4e3cf70` |
| CSV files in archive | `116` |
| Active corpus sources after inventory load | `115` |
| Active corpus rows after inventory load | `30,974` |

The local private snapshot under `var/private_corpus_snapshots/` was not deleted.

## Backup And Restore Drill

| Check | Result |
|---|---|
| Pre-import PostgreSQL backup | `/var/backups/api-quiz-bank/api_quiz_bank_pg_20260511T152132Z.dump` |
| Backup metadata | `/var/backups/api-quiz-bank/api_quiz_bank_pg_20260511T152132Z.dump.meta` |
| Backup size | `40219` bytes |
| Backup SHA-256 | `d3f3d86edba07a63bbebb9ae1aafcf77bf483e9f43925043e90a6a7f483375b2` |
| Restore drill | `postgres-restore-drill-ok api_quiz_bank_restore_drill` |
| Restore drill report | `/var/backups/api-quiz-bank/restore-drills/postgres_restore_drill_20260511T152141Z.md` |

## Corpus Import

| Check | Result |
|---|---|
| Import decision | `production_corpus_import_committed` |
| Published items | `30,974` |
| Active sources | `115` |
| Total quiz_items | `30,975` |
| Retired non-corpus items | `1` |
| Inactive non-corpus sources | `1` |
| Status counts | `published=30,974`, `retired=1` |

The retired non-corpus row is the pre-existing demo fixture row. It was removed
from delivery eligibility without editing quiz text, answers or explanations.

## Server-Side Smoke

| Check | Result |
|---|---|
| Local protected smoke script | `smoke-ok` |
| API health | `200` |
| API ready | `200` |
| No app key next-item request | `401` |
| Next item | `200` |
| Selected item status | `published` |
| Selected item id | `gmb_health_food_care_implicit_paraphrase_bank_c1_300_hfcip_187` |
| Delivery read | `200` |
| Repeat control | `200`, repeated same item `false` |
| Quota control | `429 QUOTA_EXCEEDED` |
| Entitlement negative control | `403 ENTITLEMENT_MISSING_FEATURE` |
| Cross-consumer delivery access | `404 DELIVERY_NOT_FOUND` |
| Production monitor snapshot | `/var/log/api-quiz-bank/monitoring/production_monitor_20260511T153224Z.md` |

Runtime delivery evidence after smoke:

| Check | Result |
|---|---|
| Deliveries | `2` |
| Selection decisions | `3` |

## Rollback Path

If the corpus import or smoke must be rolled back, keep the public route
protected and restore the pre-import PostgreSQL backup:

```bash
cd /opt/api-quiz-bank
set -a
. ./.env
set +a
docker exec api-quiz-bank-postgres dropdb -U "$API_QUIZ_BANK_POSTGRES_USER" --if-exists "$API_QUIZ_BANK_POSTGRES_DB"
docker exec api-quiz-bank-postgres createdb -U "$API_QUIZ_BANK_POSTGRES_USER" "$API_QUIZ_BANK_POSTGRES_DB"
docker exec -i api-quiz-bank-postgres pg_restore \
  -U "$API_QUIZ_BANK_POSTGRES_USER" \
  -d "$API_QUIZ_BANK_POSTGRES_DB" \
  < /var/backups/api-quiz-bank/api_quiz_bank_pg_20260511T152132Z.dump
sh scripts/api_quiz_bank_smoke.sh
sh scripts/api_quiz_bank_production_monitor_snapshot.sh
```

If code rollback is required, retag or rebuild the last known-good runtime image
and rerun the same smoke checks before accepting traffic.

## Boundary

No broad public launch was executed. The existing protected route and API-key
requirements remain in place. No quiz text, answers or explanations were edited.
No legal/privacy claims were expanded.
