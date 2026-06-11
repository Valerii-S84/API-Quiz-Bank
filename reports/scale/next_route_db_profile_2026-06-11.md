# `/v1/quiz-items/next` DB Profile

This profile is based on the production code path and sanitized production DB
diagnostics from 2026-06-11. It does not include secrets, headers or quiz
content.

## Per Successful Request

The route performs about 11 DB executions:

| Area | Operation | Type |
|---|---|---|
| Auth | credential lookup by consumer and key prefix | read |
| Scope | active consumer lookup | read |
| Scope | active entitlement lookup | read |
| Quota | quota upsert | write |
| Diagnostics | candidate count | read |
| Selection | eligible candidate fetch | read |
| Diagnostics | non-deliverable status count | read |
| Diagnostics | repeat-policy block count | read |
| Delivery | delivery insert | write |
| Delivery | delivery reload by id | read |
| Decision log | selection decision insert | write |

The synchronous write count is 3 per successful delivery:

- `quota_usage` upsert;
- `deliveries` insert;
- `selection_decisions` insert.

## Hot Query

The hot query is the eligible candidate fetch. It:

- reads deliverable quiz items and source metadata;
- left joins image quality policy;
- applies repeat-policy exclusion;
- fetches all eligible candidates into Python;
- computes delivery history using correlated aggregate subqueries:
  delivery count, last delivery timestamp and theme/pattern cell delivery count;
- orders by item id before Python-side weighted scoring.

No `ORDER BY RANDOM()` was found.

## Production Plan Evidence

`EXPLAIN (FORMAT JSON)` without `ANALYZE`:

| Query | Total cost | Plan rows | Notable nodes |
|---|---:|---:|---|
| candidate_count_unfiltered | 6847.79 | 1 | Hash Join; Seq Scan `quiz_items`; Seq Scan `sources` |
| eligible_select_unfiltered | 31963340.72 | 30366 | Merge Join; Anti Join; Index Scan `quiz_items_pkey`; correlated aggregate subplans; Seq Scan `deliveries` |
| repeat_count_unfiltered | 16.91 | 1 | Index Scan `idx_deliveries_consumer_item`; Index Scan `quiz_items_pkey`; Index Scan `sources_pkey` |

## Index State

Useful existing indexes:

- `idx_quiz_items_delivery_filter` on status/level/theme/objective/pattern;
- `idx_deliveries_consumer_item` on consumer/item;
- `idx_api_credentials_consumer_prefix`;
- unique quota index on consumer/feature/date;
- `quiz_item_image_quality_policy_pkey`.

Missing or suspect for the hot path:

- `deliveries(quiz_item_id)`;
- `deliveries(quiz_item_id, selected_at DESC)`;
- `deliveries(consumer_id, delivery_status, quiz_item_id)`;
- compact pre-aggregated delivery stats by item and by theme/pattern cell.

## Conclusion

The route is CPU-bound in Postgres for unfiltered selection because it repeatedly
derives delivery-history statistics while scanning a large candidate set. The
fix should reduce candidate rows and make delivery-history lookups indexed or
precomputed before any staged production load test is retried.
