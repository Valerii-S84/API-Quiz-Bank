# Next Route Hotfix Deploy Plan - 2026-06-11

Status: `Prepared; not executed`.

This plan deploys the `/v1/quiz-items/next` hotfix only after the dirty
worktree gate is explicitly resolved. It does not approve broader launch, paid
pilot readiness or a full staged load test.

## Target

| Item | Value |
|---|---|
| Runtime path | `/opt/api-quiz-bank` |
| Old server SHA | `904babbd998adcf43cfbc7945d5f24d499ec47c4` |
| Target branch | `origin/release/next-route-hotfix-2026-06-11` |
| Target hotfix SHA | `9cfdc8ebefa452bd41bb094726068379bca748ca` |
| API container | `api-quiz-bank-pilot` |
| PostgreSQL container | `api-quiz-bank-postgres` |
| PostgreSQL restart | not needed and not allowed |

## Required Pre-Deploy Gates

1. Production health remains good: API/PostgreSQL healthy and health/ready
   `200/200`.
2. Dirty worktree is resolved through one approved option from
   `reports/scale/server_dirty_worktree_review_2026-06-11.md`.
3. `git status --short` is clean except documented server-only untracked runtime
   files, if any.
4. Target SHA is verified after fetch:

```bash
cd /opt/api-quiz-bank
git fetch origin main release/next-route-hotfix-2026-06-11
git rev-parse origin/release/next-route-hotfix-2026-06-11
```

Expected target:

```text
9cfdc8ebefa452bd41bb094726068379bca748ca
```

## Deploy Commands

Run only after the pre-deploy gates pass:

```bash
cd /opt/api-quiz-bank
git checkout -B release/next-route-hotfix-2026-06-11 \
  origin/release/next-route-hotfix-2026-06-11
git status --short
docker compose \
  -f docker-compose.api-quiz-bank.yml \
  -f docker-compose.api-quiz-bank.postgres.yml \
  -f docker-compose.api-quiz-bank.secrets.yml \
  up --build -d api-quiz-bank
```

This rebuilds/recreates only the API service. It must not restart PostgreSQL.

## Migration `011`

The API image `CMD` runs `python -m quizbank_mvp.cli init-db` before Uvicorn.
With PostgreSQL runtime configuration present, that applies pending
`database/postgresql/*.sql` migrations through `schema_migrations`.

Expected migration:

```text
011_add_next_route_selection_indexes.sql
```

Expected indexes:

- `idx_quiz_items_selection_pool`
- `idx_quiz_items_cell_lookup`
- `idx_deliveries_item`
- `idx_deliveries_item_selected_at`
- `idx_deliveries_consumer_status_item`
- `idx_deliveries_consumer_item_selected_at`
- `idx_entitlements_consumer_feature_status`

Index verification should be done through the API container runtime connection,
printing only index names and boolean status.

## Post-Deploy Smoke

Run only the small protected smoke, not the full staged load test:

1. Warm-up: 5 sequential requests.
2. Main smoke: 50 sequential requests.
3. Optional: concurrency 3, 30 total requests.

Measure:

- request count and status distribution;
- latency p50/p90/p95/p99/max;
- candidate count max;
- delivery writes, selection decision writes and quota increments;
- PostgreSQL/API CPU before/during/after;
- DB connections and ungranted locks;
- health before/after.

Stop conditions:

- any 5xx;
- timeout;
- p95 > `1500 ms`;
- p99 > `3000 ms`;
- PostgreSQL CPU sustained near `100%`;
- API/PostgreSQL unhealthy;
- error/timeout spike in logs.

## Rollback

If deploy or smoke fails:

```bash
cd /opt/api-quiz-bank
git checkout -B rollback-next-route-2026-06-11 904babbd998adcf43cfbc7945d5f24d499ec47c4
docker compose \
  -f docker-compose.api-quiz-bank.yml \
  -f docker-compose.api-quiz-bank.postgres.yml \
  -f docker-compose.api-quiz-bank.secrets.yml \
  up --build -d api-quiz-bank
```

Then verify API/PostgreSQL container health and health/ready `200/200`.

Rollback should not drop the new indexes by default. Index removal would be a
separate PostgreSQL schema change and requires explicit approval.

## Explicit Non-Actions In This Task

- No production deploy.
- No migration `011` execution.
- No API/PostgreSQL restart, rebuild or recreate.
- No cleanup of server dirty files.
- No test consumer, credential or smoke write.
