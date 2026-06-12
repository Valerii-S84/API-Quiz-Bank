# Read Path CPU Remediation - 2026-06-12

## Scope

Optimize the CPU-heavy synchronous read path for `POST /v1/quiz-items/next`
after the quota-lock fix. Production was not deployed, restarted, rebuilt or
load-tested in this task.

## Baseline

The post-quota-fix production diagnostics showed the lock issue was no longer
primary:

| Probe | Result |
|---|---:|
| quota lock probe | 1200/1200 `200`, blocked locks `0` |
| quota lock probe p95 | `2373.93 ms` |
| quota lock probe Postgres CPU max | `101.46%` |
| CPU diagnostic probe | 461/461 `200`, blocked locks `0` |
| CPU diagnostic p95 | `2159.653 ms` |
| CPU diagnostic Postgres CPU max | `103.13%` |
| candidate count | `300/300` |

Root cause remained the synchronous read side: bounded candidate selection plus
delivery-history grouped metric lookups under concurrency.

## Code Remediation

Changed `src/quizbank_mvp/selection_eligibility.py`:

- reduced `CANDIDATE_POOL_LIMIT` from `300` to `150`;
- added explicit `HISTORY_SCORING_CANDIDATE_LIMIT = 24`;
- preserved indexed repeat-policy anti-join before candidate selection;
- kept `first_eligible` as a no-history-metrics compatibility path;
- limited delivery-history item metrics to the short weighted scoring window;
- removed the theme/pattern cell grouped aggregate from the synchronous hot
  path.

The duplicate/repeat guard remains in the candidate query. Quota enforcement
remains in the write transaction through the existing atomic quota reservation.

## DB Work Per Success

Local instrumentation over the full FastAPI route recorded:

| Metric | After |
|---|---:|
| sequential requests | `100` |
| status | `100/100 200` |
| SQL executions per successful route request | `8` |
| candidate max | `150` |
| history metric IDs per weighted request | `24` |
| synchronous cell grouped metrics | `0` |

The route still performs separate auth, read and write phases; this task did
not merge auth into selection or change API credential logic.

## Local Performance Proof

Evidence: `reports/scale/read_path_perf_after_fix_2026-06-12.json`.

| Metric | Result |
|---|---:|
| synthetic published items | `30000` |
| sequential `/next` requests | `100` |
| status | `100/100 200` |
| 5xx / exceptions / timeouts | `0 / 0 / 0` |
| p50 | `116.425 ms` |
| p95 | `134.965 ms` |
| p99 | `145.406 ms` |
| candidate max | `150` |
| query count per success | `8` |

Short local concurrent probe:

| Metric | Result |
|---|---:|
| workers / requests | `4 / 24` |
| status | `24/24 200` |
| 5xx / exceptions / timeouts | `0 / 0 / 0` |
| p95 | `1278.596 ms` |
| candidate max | `150` |

The concurrent probe is local SQLite/TestClient evidence only. It is not a
PostgreSQL or staging scale claim.

## Tests

Updated tests cover:

- candidate pool limit does not exceed `150`;
- delivery-history metrics are loaded only for the scoring shortlist;
- 30k synthetic item regression keeps candidate count at the new limit;
- repeat protection still excludes delivered items;
- quota enforcement still blocks over-quota delivery;
- no delivery/quota row is written when quota is denied;
- active entitlement and eligibility/status checks remain enforced;
- PostgreSQL adapter boundary remains free of SQLite-only SQL.

## Verification Snapshot

Completed before this report:

- `python3 -m py_compile src/quizbank_mvp/selection_eligibility.py tests/test_next_route_selection_performance.py tests/test_database_backend_contract.py`
- `python3 -m unittest tests.test_next_route_selection_performance tests.test_next_route_quota_lock tests.test_database_backend_contract -q` -> 25 tests OK
- `python3 tools/run_next_route_read_path_perf.py` -> local JSON evidence written
- JSON parse for `reports/scale/read_path_perf_after_fix_2026-06-12.json` -> passed

Full repository verification is recorded separately in the final task result.

## Boundaries

No production deploy, production load test, production restart/rebuild,
PostgreSQL restart, migration, secret inspection or quiz content export was
performed.
