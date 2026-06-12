# Load Bottleneck Diagnostics 2026-06-11

Status: `Done` for diagnostics. Full staged load remains `not passed`.

## Finding

The Postgres CPU spike is real but bursty. It appears during each unfiltered
`/v1/quiz-items/next` request and recovers after the request/pause. No blocked
locks, connection exhaustion, container unhealthy state or repeated 5xx were
observed.

Confirmed root cause: the unfiltered selection hot path fetches and scores about
30k deliverable quiz rows and includes correlated delivery-history aggregates per
candidate. The EXPLAIN plan for the unfiltered eligible select has total cost
`31963340.72` and includes `deliveries` seq scans inside correlated aggregate
subplans.

## Micro-Probe

| Step | Requests | Status | p50 ms | p95 ms | Max ms |
|---|---:|---|---:|---:|---:|
| diag_5 | 5 | 5x 200 | 9273.960 | 9435.122 | 9810.686 |
| diag_10 | 10 | 10x 200 | 9381.716 | 9708.471 | 9727.744 |
| diag_5_to_20_total | 5 | 5x 200 | 9290.116 | 9290.937 | 9645.745 |
| total | 20 | 20x 200 | 9290.937 | 9727.744 | 9810.686 |

Observed CPU during probe:

| Component | Max observed |
|---|---:|
| Postgres | about 101.41% |
| API | about 53.59% |

Writes stayed isolated to `load-diagnostic-2026-06-11`: 20 deliveries,
20 selection decisions and 20 quota increments. The diagnostic credential was
revoked and the raw key file was removed.

## Plan

1. Remove correlated delivery-history aggregates from the candidate SELECT.
2. Add/validate delivery-history indexes for `deliveries(quiz_item_id)`,
   `deliveries(quiz_item_id, selected_at DESC)` and
   `deliveries(consumer_id, delivery_status, quiz_item_id)`.
3. Stop fetching/scoring the full 30k candidate set per request; use bounded
   SQL-side preselection or a compact candidate pool.
4. Move `blocked_reason_counts` diagnostics off the synchronous hot path or
   sample them.
5. Repeat only a micro-probe after remediation before any Stage 1-5 load test.

One credential cannot prove the requested full profile under the effective
`120 requests / 60 seconds` rate limit. Multi-key simulation should wait until
the DB bottleneck is fixed; otherwise it hides the route-level bottleneck.
