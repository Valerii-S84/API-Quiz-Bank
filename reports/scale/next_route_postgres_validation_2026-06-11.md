# Next Route PostgreSQL Validation - 2026-06-11

Status: `Partial`.

Scope: owner-operated protected production API runtime at `/opt/api-quiz-bank`.
This validation was read-only. No production data was changed, no PostgreSQL
restart was performed, and no secrets, raw headers or quiz content were printed.

## Local Preflight

| Check | Result |
|---|---|
| Local host/user/path | `DESKTOP-LLPPQ70` / `serputko` / `/mnt/c/Users/User/Desktop/API Quiz Bank` |
| Local branch | `codex/release-governance-evidence` |
| Local SHA | `9cfdc8ebefa452bd41bb094726068379bca748ca` |
| Local status | clean |
| Expected fix files | present |
| Candidate pool limit | `300` in `src/quizbank_mvp/selection_eligibility.py` |
| Local tests | `python3 -m unittest discover -s tests -p "test_*.py"` -> `Ran 372 tests ... OK` |
| Secret scan | `python3 tools/no_secrets_scan.py` -> `No committed secrets detected.` |
| Whitespace check | `git diff --check` -> pass |

## Production Read-Only Preflight

| Check | Result |
|---|---|
| Server host/user/path | `ubuntu-8gb-nbg1-1` / `root` / `/opt/api-quiz-bank` |
| Server branch | `main` |
| Server old SHA | `904babbd998adcf43cfbc7945d5f24d499ec47c4` |
| Server `origin/main` before fetch | `904babbd998adcf43cfbc7945d5f24d499ec47c4` |
| Worktree status | dirty: 2 tracked files, 0 untracked files |
| Dirty tracked files | `src/quizbank_mvp/trusted_delivery.py`, `tests/test_shorts_factory_backend.py` |
| API container | `api-quiz-bank-pilot`, `running/healthy`, restart count `0` |
| PostgreSQL container | `api-quiz-bank-postgres`, `running/healthy`, restart count `0` |
| Local health/ready | `200` / `200` |
| Protected public health/ready | `200` / `200`; secret available: `true` |
| Resource baseline | API CPU `0.19%`, PostgreSQL CPU `3.83%`, loadavg `0.34 0.27 0.27` |
| Runtime database configuration present | `true`; value not printed |

## Migration Safety

`database/postgresql/011_add_next_route_selection_indexes.sql` was inspected
locally. It contains only `CREATE INDEX IF NOT EXISTS` statements for:

- `idx_quiz_items_selection_pool`
- `idx_quiz_items_cell_lookup`
- `idx_deliveries_item`
- `idx_deliveries_item_selected_at`
- `idx_deliveries_consumer_status_item`
- `idx_deliveries_consumer_item_selected_at`
- `idx_entitlements_consumer_feature_status`

No `DROP`, `DELETE`, `TRUNCATE`, data update or destructive schema operation was
present.

## Production PostgreSQL State Before Deploy

| Check | Result |
|---|---|
| Applied migrations | `001` through `010` |
| `011_add_next_route_selection_indexes.sql` applied | `false` |
| Target indexes present | `0/7` |
| Target indexes missing | all 7 target indexes |
| Total consumers | `22` |
| Non-test consumers before | `11` |
| Target test consumer exists | `0` |
| DB connections | `1` current DB connection, `1` non-idle |
| Ungranted locks | `0` |

## Current Production Query Evidence

Sanitized `EXPLAIN (FORMAT JSON)` without `ANALYZE` was captured from the
running pre-fix production code path.

| Query | Total cost | Plan rows | Notable nodes |
|---|---:|---:|---|
| current candidate selection | `32077516.88` | `30366` | Merge Join, Nested Loop, Index Scan, Aggregate, Seq Scan, Hash Join |

The running production code did not yet contain `CANDIDATE_POOL_LIMIT` or the
post-fix `fetch_candidate_pool` function.

## Result

PostgreSQL validation confirms the production bottleneck is still present before
deploy, the target index migration is safe and not yet applied, and production
health is good. Deployment was not executed because the documented deploy path
was unsafe for a code-only hotfix; details are in
`reports/scale/next_route_production_deploy_2026-06-11.md`.
