# Production Stabilization and Quota Reservation Profile - 2026-06-16

Generated at: `2026-06-16T20:21:52Z`

Scope: stabilize the current public `https://api.valerchik.de` state, preserve
rollback availability, and profile quota reservation without changing source
code, DNS, Caddy routing, Telegram delivery flow, queue-first mode, or live
fallback.

## Current Runtime

| Field | Evidence |
|---|---|
| Public commit | `c7cd259c0834e46f19ca7bb6eb0f74f43e2a06a7` |
| Server checkout | `c7cd259c0834e46f19ca7bb6eb0f74f43e2a06a7`, detached `HEAD`, dirty status lines `0` |
| Current image | `sha256:14d0e1ce0802387c6db3da96fde728887ccd97deafe15698d00fccaf62e616ba` |
| API container | `api-quiz-bank-pilot`, `running/healthy`, restarts `0`, started `2026-06-16T16:30:12.745726274Z` |
| PostgreSQL container | `api-quiz-bank-postgres`, `running/healthy`, restarts `0` |
| API bind | `127.0.0.1:8010` |
| Public edge | `infra_caddy_prod` publishes `80/443` |
| Caddy upstream | `api.valerchik.de` block has `reverse_proxy api-quiz-bank-pilot:8000` |
| Edge gate | `api.valerchik.de` returns `401` without `X-API-Key`; key value not recorded |

## Public Route Verification

| Check | Result |
|---|---|
| `/ready` without edge key | `401` |
| `/ready` with edge key | `200`, body `{"status":"ok","checks":[{"name":"database","status":"ok"},{"name":"visual_database","status":"ok"}]}` |
| `/v1/quiz-items/next` without edge key | `401` |
| `/v1/quiz-items/next` with edge key only, no consumer API credential | `401` |

## Queue-First Smoke

One authorized public `/v1/quiz-items/next` smoke used `consumer_demo` with the
committed demo consumer key. No secret value is recorded here.

| Field | Result |
|---|---|
| HTTP status | `200` |
| Delivery id | `deliv_ec4f5861b9eb43cf` |
| Item id | `gmb_civic_service_actions_bank_a2_300_csa_267` |
| Item status | `published` |
| Language / bank / version | `de` / `german-core` / `german-core:2026-06-12-baseline` |
| Fallback reason | `None` |
| Queue linkage | `1:selq_24e0916a921c99768fd5c985:delivered` |
| Delivery row | `1:created:published` |
| `api-quiz-bank-pilot` log hits for delivery | `1` |
| Old staging log hits for delivery | `0` |
| Fallback log count during smoke window | `0` |

Additional observations:

- `production_corpus_smoke` is active but already at `10/10` quota for
  `2026-06-16`; its attempted smoke returned `429`, with no delivery row.
- `website_quiz_teaser` has an active DB credential, but the server key file
  prefix does not match that active credential; its attempted smoke returned
  `401 AUTH_INVALID_API_KEY`. No credential was changed.

## Queue Refill

Active non-Telegram API queues below target: `0`.

Targeted refill for the smoke queue:

| Field | Before | Refill result | After |
|---|---:|---:|---:|
| Queue | `selq_24e0916a921c99768fd5c985` | same | same |
| Status | `ready` | `ready` | `ready` |
| Target size | `50` | `50` | `50` |
| Actual available items | `99` | `99` | `99` |
| Added items | n/a | `0` | n/a |

The queue was already restored above target, so the scoped refill was a clean
no-op and did not require global refill.

## Proof Access Cleanup

| Consumer | Consumer status | Active credentials | Revoked credentials | Suspended credentials |
|---|---:|---:|---:|---:|
| `public_proof_c7cd259_20260616` | `suspended` | `0` | `1` | `0` |
| `next_route_perf_proof_20260616` | `suspended` | `0` | `1` | `0` |
| `load-smoke-test-runtime-tuning-20260616-01` | `suspended` | `0` | `1` | `0` |

## Timers and Backup Status

| Unit | State |
|---|---|
| `api-quiz-bank-backup.timer` | `loaded/active/enabled` |
| `api-quiz-bank-postgres-backup.timer` | `loaded/active/enabled` |
| `api-quiz-bank-production-monitor.timer` | `loaded/active/enabled` |
| `api-quiz-bank-backup.service` | `success/0/loaded/inactive` |
| `api-quiz-bank-postgres-backup.service` | `success/0/loaded/inactive` |
| `api-quiz-bank-production-monitor.service` | `success/0/loaded/inactive` |

Recent schedule snapshot:

- `api-quiz-bank-production-monitor.timer`: last `2026-06-16 20:08:06 UTC`, next `2026-06-16 20:13:06 UTC`.
- `api-quiz-bank-backup.timer`: last `2026-06-16 03:20:00 UTC`, next `2026-06-17 03:20:00 UTC`.
- `api-quiz-bank-postgres-backup.timer`: last `2026-06-16 03:20:00 UTC`, next `2026-06-17 03:20:00 UTC`.

## DB, Corpus, and Queue Counts

| Metric | Value |
|---|---:|
| `published_items` | `30974` |
| `quiz_items_total` | `30975` |
| `active_sources` | `116` |
| `sources_total` | `116` |
| `content_banks_active` | `1` |
| `content_bank_versions_active` | `1` |
| `selection_queues_ready` | `88` |
| `selection_queue_items_available` | `8534` |
| `selection_queue_items_claimed` | `0` |
| `selection_queue_items_delivered` | `520` |

## Public 20 RPS Proof Summary

This task did not rerun the 20 RPS proof. The current public proof supplied at
task start remains the accepted load evidence:

| Metric | Result |
|---|---:|
| `200` | `20` |
| Queue linkage | `20/20` |
| Fallback | `0` |
| `429` | `0` |
| Public p95 | `238 ms` |
| Quota reserve p95 bottleneck | `150.866 ms` |

The proof consumer backing this run is now suspended and its credential is
revoked.

## Rollback State

Current rollback inventory was preserved. No image or old runtime was deleted.

| Artifact | State |
|---|---|
| Current image tag | `api-quiz-bank:pilot` -> `sha256:14d0e1ce0802387c6db3da96fde728887ccd97deafe15698d00fccaf62e616ba` |
| Rollback image | `api-quiz-bank:rollback-pre-c7cd259` -> `sha256:5d1f0e80adfa88973b003e6db0aaca5c5fdec0c7c9d7173a0cc48cb17d30bb5e` |
| Additional rollback tags | `rollback-pre-d0996c8`, `rollback-pre-805ec20`, `rollback-pre-9619613`, `rollback-pre-b3b4739` present |
| Old staging runtime | `api-quiz-bank-queue-first-staging`, `running/healthy`, not receiving public smoke delivery |
| Old rollback container | `api-quiz-bank-queue-first-staging-rollback-8882023-20260615T195109Z`, exited |

Rollback path if needed:

1. Preserve current DB/backup evidence before action.
2. Keep Caddy route unchanged unless rollback requires upstream swap.
3. Recreate `api-quiz-bank-pilot` from the known rollback image/tag or checkout
   the matching old Git ref recorded with that image.
4. Verify `/ready`, unauthorized `/next`, authorized queue-first smoke, and
   queue linkage before considering rollback complete.

## Quota Reservation SQL

Current successful `/next` queue-first path:

1. `select_next_route_result` opens one DB connection/transaction for auth,
   selection, response build, and commit.
2. `select_next_item_from_postgresql_queue` runs context read.
3. It claims a queue item with `FOR UPDATE OF sqi SKIP LOCKED`.
4. It reserves quota with the SQL below.
5. It inserts delivery, updates delivery state, marks queue item delivered, and
   inserts the selection decision before commit.

Exact reservation statement shape from `src/quizbank_mvp/selection_quota.py`:

```sql
INSERT INTO quota_usage (
    quota_usage_id, consumer_id, feature, usage_date,
    language_code, content_bank_id, bank_version_id,
    used_count, quota_limit, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
ON CONFLICT(
    consumer_id,
    feature,
    usage_date,
    language_code,
    content_bank_id,
    bank_version_id
) DO UPDATE SET
    used_count = quota_usage.used_count + 1,
    quota_limit = excluded.quota_limit,
    updated_at = excluded.updated_at
WHERE quota_usage.used_count < excluded.quota_limit
RETURNING quota_usage_id, used_count, quota_limit;
```

## Quota Profile

Profile target row, selected because it is the public proof quota row and the
consumer is now suspended:

| Consumer | Feature | Date | Used / Limit | Scope |
|---|---|---|---:|---|
| `public_proof_c7cd259_20260616` | `quiz_delivery` | `2026-06-16` | `39/200` | `de/german-core/german-core:2026-06-12-baseline` |

Indexes and constraints:

- Unique conflict arbiter: `quota_usage_content_scope_key` on
  `(consumer_id, feature, usage_date, language_code, content_bank_id, bank_version_id)`.
- Non-unique duplicate index exists with the same columns:
  `idx_quota_usage_content_scope`.
- Primary key: `quota_usage_pkey` on `quota_usage_id`.

`EXPLAIN (ANALYZE, BUFFERS, VERBOSE, WAL)` was run inside
`BEGIN ... ROLLBACK` with `statement_timeout=5s` and `lock_timeout=500ms`.
Net `used_count` remained `39` after rollback.

Key profile lines:

```text
Insert on public.quota_usage (actual time=0.293..0.294 rows=1 loops=1)
Conflict Resolution: UPDATE
Conflict Arbiter Indexes: quota_usage_content_scope_key
Conflict Filter: (quota_usage.used_count < excluded.quota_limit)
Tuples Inserted: 0
Conflicting Tuples: 1
Buffers: shared hit=17 dirtied=2
WAL: records=2 fpi=1 bytes=3502
Planning Time: 0.059 ms
Execution Time: 0.389 ms
```

Locks held by the profiling transaction before rollback:

```text
relation      RowExclusiveLock on quota_usage granted
transactionid ExclusiveLock granted
virtualxid    ExclusiveLock granted
```

Concurrency lock probe on the same suspended proof quota row:

- Holder transaction updated the row and slept for `4s`, then rolled back.
- Waiter transaction attempted the same `INSERT ... ON CONFLICT DO UPDATE`
  with `lock_timeout=750ms`.
- Waiter result:

```text
ERROR: canceling statement due to lock timeout
CONTEXT: while inserting index tuple (4,62) in relation "quota_usage"
```

After both rollback paths, the quota row remained `39/200`.

Runtime connection mode:

| Field | Value |
|---|---|
| Selection mode | `queue_first` |
| Live fallback consumers | `0` |
| PostgreSQL pool enabled | `True` |
| PostgreSQL pool min/max | `1/20` |
| PostgreSQL pool timeout | `5.0s` |
| Current activity after probe | `7` idle pool sessions, no lock waits |

## Root Cause Classification

| Candidate | Classification |
|---|---|
| Single quota row lock | Proven primary cause. Concurrent requests for one consumer/date/feature/content scope serialize on the same `quota_usage` row. |
| Missing index | Not supported. The exact unique conflict index is used, and single-row execution is `0.389 ms`. |
| Transaction too wide | Contributing factor. The quota row lock is acquired before delivery finalize and decision insert, then held until the request transaction commits. |
| Connection/pool interaction | Not primary. Pool is enabled with max `20`; after profiling only idle sessions were observed and no pool wait was detected. |
| Unnecessary quota write per request | Design-level contributor. Every successful delivery increments one quota row for the current quota scope, so same-scope concurrency is inherently serialized. |
| Other | Duplicate non-unique quota scope index exists, but current evidence does not show it as the p95 cause. |

Recommendation: `C. Code-level quota reservation redesign is needed` for the
next quota bottleneck fix. No code change was made in this task.

## Not Touched

- No source code changed.
- No DNS changes.
- No Caddy routing changes.
- No deploy, restart, rebuild, or container recreation.
- No old runtime/image deletion.
- No queue-first disablement.
- No live fallback enablement.
- No Telegram containers, bots, sends, backfills, or delivery flow changes.
- No destructive SQL.
