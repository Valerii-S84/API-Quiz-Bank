# Quota Lock Remediation - 2026-06-12

Status: `Done local remediation proof`.

Scope: `/v1/quiz-items/next` quota-lock bottleneck narrowed to `quota_usage`
transaction scope during the 2026-06-12 Stage 4 diagnostics.

## Root Cause

Before this remediation, `/v1/quiz-items/next` reserved quota before candidate
selection. The same transaction then continued through delivery-history reads,
candidate scoring, delivery insert and selection-decision insert.

Captured production-safe diagnostics showed:

| Signal | Value |
|---|---|
| Blocked query type | `INSERT INTO quota_usage` |
| Lock type | `transactionid` |
| Blocked mode | `ShareLock` |
| Blocker mode | `ExclusiveLock` |
| Blocker query at sample | `SELECT FROM deliveries` |

Conclusion: the quota row update was atomic, but its lock was held too long.

## Code Change

Runtime selection flow is now split:

1. Read phase, before quota reservation:
   - active consumer and entitlement lookup;
   - scope enforcement;
   - bounded candidate pool load;
   - delivery-history metrics lookup;
   - scoring and eligibility decision;
   - no-candidate diagnostics, only when no item is selected.
2. Short write transaction:
   - atomic `quota_usage` reserve/check;
   - `deliveries` insert;
   - required `selection_decisions` insert;
   - commit.

`create_delivery()` no longer performs a post-insert `SELECT FROM deliveries`;
the delivery projection is built from the inserted values.

## Local Proof

Evidence report: `reports/scale/quota_lock_perf_after_fix_2026-06-12.json`.

Summary:

| Check | Result |
|---|---:|
| Local route probe responses | 60/60 `200` |
| 5xx / exceptions / timeouts | 0 / 0 / 0 |
| p95 | 112.823 ms |
| Candidate count max | 300 |
| Deliveries / quota used / decisions | 60 / 60 / 60 |
| Quota rows while first request was in delivery-history phase | 0 |
| Peer request completed before first delivery-history phase was released | true |
| Quota correctness in boundary probe | 2 deliveries, used count 2 |

The local p95 was below the prior protected postfix smoke p95 of 211.445 ms.
This is not a production latency claim because the proof ran locally.

## Test Coverage

Added/updated coverage:

- quota remains enforced after moving reservation later;
- exhausted quota still takes precedence over no-candidate without incrementing
  quota;
- concurrent requests do not exceed quota;
- delivery is not written when quota is denied;
- quota is rolled back when delivery insert fails;
- delivery-history reads complete before quota reservation;
- a peer request can reserve quota while another request is held in the
  delivery-history phase;
- PostgreSQL adapter regression: full `select_next_item()` uses separate read
  and write connection scopes, with delivery-history reads outside the quota
  write scope.

## Verification

Completed after the remediation:

- `python3 -m unittest discover -s tests -p "test_*.py"` -> 380 tests OK;
- `python3 tools/no_secrets_scan.py` -> no committed secrets detected;
- `git diff --check` -> pass;
- JSON parse for `reports/scale/quota_lock_perf_after_fix_2026-06-12.json`
  -> pass;
- targeted marker scan for raw keys, database URLs, credential header names and
  quiz-content markers in the new/updated quota reports -> no matches.

## Boundaries

- No production deploy.
- No production load test.
- No production restart or rebuild.
- No quota enforcement removal.
- No raw keys, database URL, credential header values or quiz content recorded.
- Local Docker and `psql` were unavailable, so no local PostgreSQL `pg_locks`
  sampler evidence was produced in this pass.
