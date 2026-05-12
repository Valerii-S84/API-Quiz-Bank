# Protected Production 100 Ready Closure

Date: 2026-05-12.

Scope: owner-operated protected production API runtime at `api.valerchik.de`
with PostgreSQL-backed promoted corpus delivery. This closure is limited to the
protected API surface and does not approve broad public launch, unauthenticated
API access, school deployment, paid launch or legal/privacy scope expansion.

## Release State

| Check | Result |
|---|---|
| Promotion evidence commit | `bbe29ec` |
| Prior deploy proof commit | `c4d1478` |
| Repeatable deploy tooling commit | `fdc890e69c7813f0c92c829ac8c74af1431603fb` |
| Release tag target | `protected-production-corpus-2026-05-12` |
| Docker base image | pinned by digest in `Dockerfile` |
| Runtime import tool | `tools/import_production_corpus_to_runtime.py` |
| Protected production smoke script | `scripts/api_quiz_bank_protected_production_smoke.sh` |

The Docker runtime no longer depends on a mutable unpinned base image resolving
the same way at rebuild time. The runtime import and protected smoke flows are
committed and repeatable.

## VPS Runtime

| Check | Result |
|---|---|
| VPS checkout | `fdc890e69c7813f0c92c829ac8c74af1431603fb` |
| API image | `sha256:fb3611d2e50cbd6456146c371f4352eaacbdd110d4565865b45f40e1f131ea89` |
| API container | `running/healthy`, restart count `0` |
| PostgreSQL container | `running/healthy`, restart count `0` |
| API host bind | `127.0.0.1:8010` |
| Public route | `https://api.valerchik.de` behind `X-API-Key` |

Server-only untracked secret and private corpus files remain outside Git.

## Corpus Import

Import was rerun through the committed runtime import tool against the private
promoted corpus snapshot staged outside Git.

| Check | Result |
|---|---|
| Import report | `/opt/api-quiz-bank/private/corpus/2026-05-11/production_corpus_runtime_import_2026-05-12.json` |
| Decision | `production_corpus_import_committed` |
| Source active rows | `30,974` |
| Source active sources | `115` |
| Published items after import | `30,974` |
| Active sources after import | `115` |
| Status counts | `published:30,974`, `retired:1` |
| Non-corpus fixture handling | one demo fixture item retired and one fixture source inactive |
| Smoke consumers | seeded for controlled production smoke |

No quiz text, answers or explanations were edited.

## Protected Smoke

| Check | Result |
|---|---|
| Smoke report | `/var/log/api-quiz-bank/monitoring/protected_production_smoke_20260512T0534.json` |
| Decision | `protected_production_smoke_ok` |
| Published items | `30,974` |
| Active sources | `115` |
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

## Backup And Restore

| Check | Result |
|---|---|
| Post-import backup | `/var/backups/api-quiz-bank/api_quiz_bank_pg_20260512T053408Z.dump` |
| Backup metadata | `/var/backups/api-quiz-bank/api_quiz_bank_pg_20260512T053408Z.dump.meta` |
| Backup size | `1,567,709` bytes |
| Backup SHA-256 | `bfeb1e26ac68c63ef968eddbfabf458f12a16281c329f3051ff3eee34ec4d663` |
| Backup restore status | `restore_tested_status=pass` |
| Restore drill report | `/var/backups/api-quiz-bank/restore-drills/postgres_restore_drill_20260512T053416Z.md` |
| Restore drill status | `pass` |
| Restore drill published items | `30,974` |
| Restore drill active sources | `115` |
| Retention | `30` days |

The rollback source for this protected production state is the post-import backup
above. The prior pre-import backup remains available at
`/var/backups/api-quiz-bank/api_quiz_bank_pg_20260511T152132Z.dump`.

## Monitoring Window

Three post-deploy production monitor snapshots passed:

| Snapshot | Result |
|---|---|
| `/var/log/api-quiz-bank/monitoring/production_monitor_20260512T053418Z.md` | `Status: ok`, failures `none` |
| `/var/log/api-quiz-bank/monitoring/production_monitor_20260512T053420Z.md` | `Status: ok`, failures `none` |
| `/var/log/api-quiz-bank/monitoring/production_monitor_20260512T053422Z.md` | `Status: ok`, failures `none` |

Latest monitor snapshot checks:

| Check | Result |
|---|---|
| Public health without edge key | `401` |
| Public health with edge key | `200` |
| Public ready with edge key | `200` |
| Public delivery without edge key | `401` |
| API container | `running/healthy` |
| PostgreSQL container | `running/healthy` |
| PostgreSQL backup timer | `active` |
| Latest PostgreSQL backup service result | `success/0` |
| API restart count | `0` |
| PostgreSQL restart count | `0` |
| Failures | `none` |

## Rollback Command

Keep the public route protected and restore the post-import backup into the
active PostgreSQL database only if rollback is explicitly required:

```bash
cd /opt/api-quiz-bank
set -a
. ./.env
set +a
docker exec api-quiz-bank-postgres dropdb \
  -U "$API_QUIZ_BANK_POSTGRES_USER" \
  --if-exists "$API_QUIZ_BANK_POSTGRES_DB"
docker exec api-quiz-bank-postgres createdb \
  -U "$API_QUIZ_BANK_POSTGRES_USER" \
  "$API_QUIZ_BANK_POSTGRES_DB"
docker exec -i api-quiz-bank-postgres pg_restore \
  -U "$API_QUIZ_BANK_POSTGRES_USER" \
  -d "$API_QUIZ_BANK_POSTGRES_DB" \
  < /var/backups/api-quiz-bank/api_quiz_bank_pg_20260512T053408Z.dump
API_QUIZ_BANK_PROTECTED_SMOKE_REPORT_PATH=/var/log/api-quiz-bank/monitoring/protected_production_smoke_after_restore.json \
  sh scripts/api_quiz_bank_protected_production_smoke.sh
sh scripts/api_quiz_bank_production_monitor_snapshot.sh
```

## Closure Decision

```text
GO: Protected Production Runtime 100 Ready for owner-operated protected API use.
NO-GO: broad public launch, unauthenticated API access, school deployment,
paid launch, or expanded legal/privacy claims without separate approval.
```

This closure proves the protected production corpus runtime, not a broad public
or commercial launch.
