# Quota Transaction Before/After - 2026-06-12

Scope: transaction boundary for `/v1/quiz-items/next` quota reservation.

## Before

```text
open DB connection / transaction scope
  load active consumer
  load active entitlement
  enforce scope
  reserve quota with INSERT INTO quota_usage ... ON CONFLICT DO UPDATE
  load bounded candidates
  read delivery history from deliveries
  score candidates
  insert delivery
  select delivery back from deliveries
  insert selection decision
commit
```

Risk: the `quota_usage` row lock was held while the request continued into
delivery-history reads and scoring. Under concurrent `/next` traffic, another
request could block on `INSERT INTO quota_usage` while the blocker was already
executing `SELECT FROM deliveries`.

## After

```text
read phase
  load active consumer
  load active entitlement
  enforce scope
  load bounded candidates
  read delivery history from deliveries
  score candidates
  choose item or, on no-candidate, check exhausted quota without reservation
  write no-candidate diagnostic outside quota path when quota is not exhausted

short write transaction
  reserve quota with INSERT INTO quota_usage ... ON CONFLICT DO UPDATE
  insert delivery
  insert required selection decision
commit
```

The write phase does not run delivery-history reads. `create_delivery()` returns
the response projection from inserted values instead of reading the delivery row
back during the quota transaction.

## Atomicity

Quota reservation remains atomic through the existing
`INSERT ... ON CONFLICT DO UPDATE ... WHERE used_count < quota_limit RETURNING`
statement.

Quota and delivery commit/rollback together in the short write transaction:

- if quota is denied, delivery is not inserted;
- if delivery insert fails after quota reserve, the quota increment rolls back;
- successful delivery increments quota exactly once.

## Diagnostics

No-candidate diagnostics remain outside the quota reservation path because no
delivery is created and quota must not be charged.

If no candidate is available, the runtime performs a cheap, non-mutating quota
read before returning the no-candidate problem. This preserves the existing
`QUOTA_EXCEEDED` precedence for already exhausted consumers without reserving
quota or taking the `quota_usage` write lock.

The success selection decision remains in the short write transaction as
required delivery evidence. It is a single insert and does not perform
delivery-history reads.

## Local Regression Evidence

- `tests/test_next_route_quota_lock.py`
- `tests/test_database_backend_contract.py`
- `reports/scale/quota_lock_perf_after_fix_2026-06-12.json`

Local boundary proof showed a peer request completing its quota reservation
while the first request was held in the delivery-history phase, with zero quota
rows visible before the first request reached the write phase.
