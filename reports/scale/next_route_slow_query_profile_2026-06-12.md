# `/v1/quiz-items/next` Slow Query Profile - 2026-06-12

Production was sampled during a short controlled CPU repro. SQL text was reduced to query type/table shape; no literals, raw headers, keys, DB URL or quiz content are included.

## Successful Request Shape

A successful `/next` request still performs about 9 DB executions:

| Area | Operation | Verdict |
|---|---|---|
| Auth | credential lookup by consumer/key prefix | visible, not primary |
| Scope | active consumer lookup | visible, not primary |
| Scope | active entitlement lookup | visible, not primary |
| Selection | bounded candidate fetch, limit 300 | primary contributor |
| Selection metrics | delivery count/last delivery grouped by candidate item | primary contributor |
| Selection metrics | theme/pattern cell delivery counts | primary contributor |
| Quota | atomic quota upsert | not primary in this repro |
| Delivery | delivery insert | not primary in this repro |
| Decision log | selection decision insert | secondary synchronous write |

## Active Query Samples

| Query type | Samples | Max query age | Wait notes |
|---|---:|---:|---|
| `SELECT FROM quiz_items` | 34 | 0.404s | Client:ClientRead=5, Client:ClientWrite=5, LWLock:LockManager=1 |
| `SELECT FROM deliveries` | 13 | 0.392s | Client:ClientRead=4 |
| `SELECT FROM api_credentials` | 10 | 0.096s | Client:ClientRead=2 |
| `INSERT INTO deliveries` | 7 | 0.204s | Client:ClientRead=3 |
| `SELECT FROM entitlements` | 5 | 0.199s | Client:ClientRead=2 |
| `BEGIN OTHER` | 3 | 0.116s | Client:ClientRead=1 |
| `INSERT INTO selection_decisions` | 3 | 0.104s | Client:ClientRead=1 |
| `SELECT FROM consumers` | 3 | 0.185s | none sampled |
| `INSERT INTO quota_usage` | 2 | 0.005s | none sampled |
| `COMMIT OTHER` | 1 | 0.002s | none sampled |

## EXPLAIN Summary

`EXPLAIN (FORMAT JSON)` was used without `ANALYZE`; no production mutation was executed for write queries.

| Query profile | Total cost | Plan rows | Index evidence | Notes |
|---|---:|---:|---|---|
| `candidate_selection` | 1082.43 | 300 | idx_deliveries_consumer_item_selected_at, idx_quiz_items_selection_pool, quiz_item_image_quality_policy_pkey, sources_pkey | uses selection pool and repeat-policy indexes, still returns 300 rows per request |
| `delivery_item_metrics` | 1178.92 | 1253 | idx_quiz_items_selection_pool, sources_pkey | planned a deliveries Seq Scan plus candidate CTE; repeated per request under concurrency |
| `delivery_cell_metrics` | 1298.81 | 198 | idx_deliveries_item, idx_quiz_items_cell_lookup, idx_quiz_items_selection_pool, sources_pkey | uses cell lookup and deliveries item indexes but still adds grouped metric cost |
| `quota_usage_lookup` | 8.29 | 1 | quota_usage_consumer_id_feature_usage_date_key | uses quota unique index |
| `entitlement_lookup` | 5.75 | 1 | none in plan | small table, not CPU-heavy |
| `auth_credential_lookup` | 9.13 | 1 | none in plan | small table, not CPU-heavy |

## Index Validation

- `quiz_items`: `idx_quiz_items_cell_lookup, idx_quiz_items_delivery_filter, idx_quiz_items_selection_pool, quiz_items_pkey`
- `deliveries`: `deliveries_pkey, idx_deliveries_consumer_item, idx_deliveries_consumer_item_selected_at, idx_deliveries_consumer_status_item, idx_deliveries_item, idx_deliveries_item_selected_at`
- `quota_usage`: `quota_usage_consumer_id_feature_usage_date_key, quota_usage_pkey`
- `selection_decisions`: `idx_selection_decisions_consumer_created, idx_selection_decisions_selected_item, selection_decisions_pkey`
- `entitlements`: `entitlements_pkey, idx_entitlements_consumer_feature_status`
- `api_credentials`: `api_credentials_consumer_id_key_prefix_key, api_credentials_pkey, idx_api_credentials_consumer_prefix`
- `consumers`: `consumers_pkey`

## Conclusion

No missing index is proven by this run. The expected next-route indexes are present, but the read path remains CPU-bound because every request performs indexed candidate selection plus grouped delivery-history lookups over the current delivery table. The highest-signal remediation is to reduce the candidate pool and precompute or batch delivery-history metrics, then rerun the same short probe before any Stage 4/Stage 5 gate.
