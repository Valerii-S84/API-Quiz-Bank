# `/v1/quiz-items/next` Remediation 2026-06-11

Status: `Done` for local code remediation and local performance proof.
Production was not redeployed, restarted, queried or load-tested.

## Root Cause

The hot selection query fetched the full eligible bank into Python and scored it
there. On the production corpus path this meant about 30k rows per unfiltered
request. The same query also computed delivery history through correlated
aggregate subqueries per candidate:

- item delivery count;
- item last delivery timestamp;
- theme/pattern cell delivery count.

Baseline production diagnostic cost for the old eligible select:
`31963340.72`.

## Code Remediation

Changed runtime selection logic in `src/quizbank_mvp/selection_eligibility.py`:

- candidate pool is bounded by `CANDIDATE_POOL_LIMIT = 300`;
- repeat protection uses an indexed `LEFT JOIN deliveries d_repeat ... IS NULL`
  anti-join instead of a correlated repeat subquery in the hot select;
- delivery-history scoring metrics are loaded after candidate bounding with
  grouped lookups over the bounded candidate IDs and candidate cells;
- Python scoring still uses the existing weighted scorer, but never receives
  more than the bounded pool.

Changed orchestration in `src/quizbank_mvp/selection.py`:

- successful selections no longer run synchronous full diagnostic count scans;
- full diagnostic counts remain on the no-candidate path for failure evidence.

Synchronous writes remain limited to the critical response path:

- `quota_usage` upsert;
- `deliveries` insert;
- `selection_decisions` insert.

## Index Remediation

Added idempotent migrations:

- `database/migrations/010_add_next_route_selection_indexes.sql`;
- `database/postgresql/011_add_next_route_selection_indexes.sql`.

New indexes cover:

- bounded quiz item pool lookup;
- theme/pattern cell lookup;
- item delivery stats;
- repeat lookup by consumer/status/item;
- consumer/item/date lookup;
- active entitlement lookup.

## Local Performance Proof

Report: `reports/scale/next_route_perf_after_fix_2026-06-11.json`

Local synthetic proof used 30,000 published items, 100 sequential `/next`
requests, FastAPI TestClient and SQLite runtime.

| Metric | Result |
|---|---:|
| Status | 100/100 `200` |
| 5xx/timeouts | 0 / 0 |
| p50 | 143.570 ms |
| p95 | 160.956 ms |
| p99 | 181.600 ms |
| max | 192.371 ms |
| Max candidate count recorded | 300 |
| Distinct selected items | 100 / 100 |

Local proof decision: `GO local remediation proof`.

## Verification

Local checks completed:

- `python3 -m unittest discover -s tests -p "test_*.py"` -> 372 tests OK;
- `python3 tools/no_secrets_scan.py` -> no committed secrets detected;
- `git diff --check` -> no whitespace errors;
- local report marker scan found no raw key/header/content markers in the new
  scale proof reports.

## Limits

Local Docker/PostgreSQL was unavailable in this WSL environment, so a new local
PostgreSQL `EXPLAIN` cost was not produced. The after evidence is SQLite
`EXPLAIN QUERY PLAN` plus local route latency proof. Production paid pilot
readiness is not claimed until a post-fix protected production smoke/load run is
approved and completed.
