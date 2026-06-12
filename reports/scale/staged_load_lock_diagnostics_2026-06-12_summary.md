# Staged Load Lock Diagnostics - 2026-06-12

## Scope

Production-safe diagnosis of Stage 4 blocked DB locks after the protected staged
load for `/v1/quiz-items/next`.

No deploy, rebuild, restart, migration, full staged load or Stage 5 soak was
performed. The probe used isolated diagnostic credentials only; no real
consumer was touched and no secret values or quiz content were emitted.

## Existing Stage 4 Evidence

| Field | Value |
|---|---:|
| Stage | `stage_4_strong_safe_load` |
| Started | `2026-06-12T08:03:48Z` |
| Stopped | `2026-06-12T08:07:17Z` |
| Stop condition | `stopped_blocked_locks` |
| Requests | `1943` |
| Statuses | `{"200": 1942, "502": 1}` |
| p95 / p99 / max | `1241.206 / 1842.176 / 2457.567 ms` |
| DB connections max | `26` |
| Blocked locks max | `2` |
| Blocking sessions max | `2` |
| Postgres CPU max | `35.22%` |
| API CPU max | `20.28%` |
| Candidate count max | `300` |

The original reports do not contain per-request records, so the exact client-side
timestamp of the single `502` is not recoverable from the committed artifacts.
API and Postgres container logs for the Stage 4 window showed no app-side 5xx,
traceback or Postgres error.

## Controlled Probe

| Field | Value |
|---|---:|
| Run id | `lock_diag_20260612T083653Z_700f4f98` |
| Window | `2026-06-12T08:36:53Z` - `2026-06-12T08:36:59Z` |
| Isolated consumers | `20` |
| Target | `20 rps`, max `90s` |
| Stop reason | `blocked_locks_detected` |
| Requests | `31` |
| Statuses | `{"200": 31}` |
| Timeouts / 5xx | `0 / 0` |
| p95 / max | `1157.611 / 1225.562 ms` |
| DB connections max | `11` |
| Blocked locks max | `1` |
| Probe credentials after cleanup | `0 active`, revoked-key check `403` |

## Lock Evidence

| Field | Value |
|---|---|
| Sample time | `2026-06-12T08:36:55.048Z` |
| Blocked PID / blocker PID | `2784254 / 2784258` |
| Lock type | `transactionid` |
| Blocked lock mode | `ShareLock` |
| Blocker lock mode | `ExclusiveLock` |
| Blocked wait event | `Lock:transactionid` |
| Blocked query type | `INSERT INTO quota_usage` |
| Blocker query type at sample | `SELECT FROM deliveries` |
| Blocked transaction age | `0.420s` |
| Blocker transaction age | `0.284s` |

## Root Cause

The blocked lock is the quota reservation path. A request blocks while executing
the atomic `quota_usage` insert/update. The blocker has already reserved quota
and moved on to delivery-history reads, but it still holds the quota row
transaction lock because the transaction remains open through selection,
delivery insert and selection-decision insert.

Classification:

- Quota update: confirmed.
- Delivery insert: not the blocking query.
- Selection decision insert: not the blocking query.
- Entitlement lookup/update: not the blocking query.
- Diagnostics/logging write: not involved.
- Monitoring probe: not the blocker.
- Transaction boundary: too broad after quota update.

## Remediation Plan

1. Keep quota accounting atomic, but move it into a short transaction that does
   not cover candidate selection and delivery-history reads.
2. Prefer read-only candidate selection before quota reservation, then reserve
   quota and write delivery evidence in the smallest possible write section.
3. If needed, defer or make `selection_decisions` cheaper after delivery is
   durable.
4. Keep diagnostics read-only and outside the synchronous `/next` path.
5. After a scoped fix and approved deploy window, rerun the short lock probe
   before rerunning Stage 4 and Stage 5 gates.

## Final Sanity

| Check | Result |
|---|---:|
| health / ready | `200 / 200` |
| API restart count | `0` |
| Postgres restart count | `0` |
| DB connections | `1` |
| Blocked locks | `0` |
| Blocking sessions | `0` |
| Non-test consumers | `23` |
| Active probe credentials | `0` |
