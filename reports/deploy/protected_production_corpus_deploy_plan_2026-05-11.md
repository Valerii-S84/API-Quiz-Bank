# Protected Production Corpus Deploy Plan

Date: 2026-05-11.

Scope: controlled VPS PostgreSQL production runtime update for the promoted
QuizBank corpus. This plan preserves the existing protected API boundary and
does not approve unauthenticated public access, broad public launch, school
deployment, paid launch or legal/privacy expansion.

## Promotion Evidence

| Check | Value |
|---|---|
| Promotion report | `reports/publication/verified_corpus_promotion_2026-05-11.json` |
| Owner approval | `reports/publication/owner_corpus_approval_2026-05-11.json` |
| PostgreSQL smoke report | `reports/imports/production_corpus_postgresql_smoke_2026-05-11.json` |
| Active source files | `115` |
| Active rows | `30,974` |
| Published rows | `30,974` |
| Production corpus gate | `GO` |
| PostgreSQL smoke | `GO` |
| Content fields changed | `false` |

Private corpus snapshot evidence is stored outside Git because `QuizBank/` is
ignored:

| Artifact | Path |
|---|---|
| CSV checksum manifest | `var/private_corpus_snapshots/quizbank_csv_sha256_2026-05-11.txt` |
| CSV archive | `var/private_corpus_snapshots/quizbank_csv_promoted_snapshot_2026-05-11.tar.gz` |
| CSV archive checksum | `var/private_corpus_snapshots/quizbank_csv_promoted_snapshot_2026-05-11.tar.gz.sha256` |
| Snapshot summary | `var/private_corpus_snapshots/quizbank_private_snapshot_summary_2026-05-11.txt` |

## Preconditions

1. Work only inside the existing VPS runtime path:
   `/opt/api-quiz-bank`.
2. Keep Caddy `X-API-Key` protection enabled for `api.valerchik.de`.
3. Keep application credentials protected by `X-Consumer-Id` and
   `X-QuizBank-API-Key`.
4. Do not copy private `QuizBank/*.csv` through GitHub.
5. Do not edit quiz text, answers, explanations or source wording during deploy.
6. Stop if any verification step fails.

## Backup Current VPS PostgreSQL

Run before any runtime corpus import:

```bash
cd /opt/api-quiz-bank
API_QUIZ_BANK_BACKUP_DIR=/var/backups/api-quiz-bank \
  ./scripts/api_quiz_bank_postgres_backup.sh
```

Record the returned backup path and metadata path. Verify the dump is non-empty:

```bash
test -s /var/backups/api-quiz-bank/api_quiz_bank_pg_YYYYMMDDTHHMMSSZ.dump
test -s /var/backups/api-quiz-bank/api_quiz_bank_pg_YYYYMMDDTHHMMSSZ.dump.meta
```

Run an isolated restore drill before import:

```bash
API_QUIZ_BANK_POSTGRES_BACKUP_PATH=/var/backups/api-quiz-bank/api_quiz_bank_pg_YYYYMMDDTHHMMSSZ.dump \
API_QUIZ_BANK_RESTORE_DRILL_REPORT_DIR=/var/backups/api-quiz-bank/restore-drills \
  ./scripts/api_quiz_bank_postgres_restore_drill.sh
```

## Import Promoted Corpus

1. Transfer the private promoted corpus snapshot to the VPS through an
   operator-controlled channel outside Git.
2. Verify the snapshot checksum against:
   `var/private_corpus_snapshots/quizbank_csv_promoted_snapshot_2026-05-11.tar.gz.sha256`.
3. Extract to a private runtime staging directory, for example:
   `/opt/api-quiz-bank/private/QuizBank-promoted-2026-05-11`.
4. Run the corpus import in a single transaction against PostgreSQL using the
   same source parsing and runtime upsert path proven by
   `tools/run_production_corpus_postgresql_smoke.py`.
5. Commit the transaction only after the post-import count checks below pass.

The import must upsert `sources` and `quiz_items` only. It must not modify
consumer credentials, Caddy configuration, Telegram configuration, legal/privacy
documents, or launch settings.

## Required Verification

Run these checks on the VPS immediately after import and before declaring the
runtime updated:

```bash
docker exec -i api-quiz-bank-postgres psql -U api_quiz_bank -d api_quiz_bank -t -A <<'SQL'
SELECT COUNT(*) FROM quiz_items WHERE status = 'published';
SELECT COUNT(*) FROM sources WHERE status = 'active';
SELECT status, COUNT(*) FROM quiz_items GROUP BY status ORDER BY status;
SQL
```

Expected values:

| Check | Expected |
|---|---|
| Published quiz items | `30974` |
| Active sources | `115` |
| Non-published deliverable corpus rows | `0` |

Run protected API smoke:

```bash
cd /opt/api-quiz-bank
./scripts/api_quiz_bank_smoke.sh
./scripts/api_quiz_bank_production_monitor_snapshot.sh
```

Expected result:

| Check | Expected |
|---|---|
| API smoke | `smoke-ok` |
| `/health` behind protected route | `200` with edge key |
| `/ready` behind protected route | `200` with edge key |
| No edge key | `401` |
| API container | `running/healthy` |
| PostgreSQL container | `running/healthy` |
| PostgreSQL backup timer | `active` |

## Rollback

If import or smoke fails, keep the public route protected and restore the
pre-import PostgreSQL backup:

```bash
cd /opt/api-quiz-bank
docker exec api-quiz-bank-postgres dropdb -U api_quiz_bank --if-exists api_quiz_bank
docker exec api-quiz-bank-postgres createdb -U api_quiz_bank api_quiz_bank
docker exec -i api-quiz-bank-postgres pg_restore -U api_quiz_bank -d api_quiz_bank \
  < /var/backups/api-quiz-bank/api_quiz_bank_pg_YYYYMMDDTHHMMSSZ.dump
./scripts/api_quiz_bank_smoke.sh
./scripts/api_quiz_bank_production_monitor_snapshot.sh
```

Rollback source path:
`/var/backups/api-quiz-bank/api_quiz_bank_pg_YYYYMMDDTHHMMSSZ.dump`.

If code rollback is also required, use the last known good protected production
commit recorded in
`reports/roadmap/production_postgresql_runtime_closure_2026-05-10.md`, then
rebuild the existing compose stack and rerun the same smoke checks.

## No Broad Public Launch

This plan does not change public access policy. The VPS may remain available
only through the existing protected route. Do not remove the edge key, do not
open unauthenticated API traffic, do not start school/paid/external launch, and
do not expand legal/privacy claims as part of this corpus deploy.
