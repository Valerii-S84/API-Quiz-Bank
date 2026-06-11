# `/v1/quiz-items/next` Explain Before/After 2026-06-11

Production was not touched. This report combines the previously recorded
production baseline with local SQLite `EXPLAIN QUERY PLAN` evidence after the
fix.

## Before Baseline

From `reports/scale/next_route_db_profile_2026-06-11.md`:

| Query | PostgreSQL total cost | Plan rows | Notes |
|---|---:|---:|---|
| `candidate_count_unfiltered` | 6847.79 | 1 | Hash join; seq scans |
| `eligible_select_unfiltered` | 31963340.72 | 30366 | Correlated delivery aggregate subplans |
| `repeat_count_unfiltered` | 16.91 | 1 | Indexed repeat count |

Local SQLite before-shape plan over a synthetic 30k set showed the same
structural issue:

```text
CORRELATED SCALAR SUBQUERY 1
SEARCH d_all USING COVERING INDEX idx_deliveries_item
CORRELATED SCALAR SUBQUERY 2
SEARCH d_last USING COVERING INDEX idx_deliveries_item_selected_at
CORRELATED SCALAR SUBQUERY 3
SEARCH d_cell USING COVERING INDEX idx_deliveries_item
USE TEMP B-TREE FOR ORDER BY
```

## After Local Plan

The fixed candidate query is bounded with `LIMIT 300`, uses the new selection
pool index, and has no correlated aggregate subqueries:

```text
SEARCH qi USING INDEX idx_quiz_items_selection_pool
SEARCH s USING INDEX sqlite_autoindex_sources_1
SEARCH iq USING INDEX sqlite_autoindex_quiz_item_image_quality_policy_1 LEFT-JOIN
SEARCH d_repeat USING COVERING INDEX idx_deliveries_consumer_status_item LEFT-JOIN
```

The grouped delivery metric lookups are separate bounded/filtered reads:

```text
SEARCH deliveries USING COVERING INDEX idx_deliveries_item_selected_at
SEARCH qi USING COVERING INDEX idx_quiz_items_cell_lookup
SEARCH d USING COVERING INDEX idx_deliveries_item
```

## Cost Evidence Boundary

New local PostgreSQL cost: `not available`.

Reason: Docker/PostgreSQL was unavailable in this WSL environment, and production
was not touched. The committed evidence therefore proves the code path no longer
fetches/scores 30k candidates locally and no longer contains the old correlated
aggregate subplans in the hot candidate query; it does not claim a post-fix
production PostgreSQL cost.

The post-fix local route proof is stored in:

- `reports/scale/next_route_perf_after_fix_2026-06-11.json`
