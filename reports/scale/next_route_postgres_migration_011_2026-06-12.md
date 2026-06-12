# Next Route PostgreSQL Migration 011 - 2026-06-12

## Scope

Apply only `database/postgresql/011_add_next_route_selection_indexes.sql` on the
production PostgreSQL container for the `/v1/quiz-items/next` hotfix.

Postgres was not restarted.

## Preflight

| Check | Result |
|---|---|
| Host | `valerchik.de` |
| Path | `/opt/api-quiz-bank` |
| Server branch | `release/next-route-hotfix-2026-06-11` |
| Server SHA | `9cfdc8ebefa452bd41bb094726068379bca748ca` |
| Applied `001`-`010` | `10` |
| Applied `011` before | `0` |
| Migration file hash | `08fab06ceb32597d5abdfa1df7c63e0137ab0593f2f9ad94c04b61c7dce97ef7` |

## Safety Review

| Pattern | Count |
|---|---:|
| `CREATE INDEX IF NOT EXISTS` | 7 |
| `DROP` | 0 |
| `DELETE` | 0 |
| `TRUNCATE` | 0 |
| `ALTER` | 0 |

The migration is non-destructive and only adds indexes if absent.

## Application

The migration was applied through the existing Postgres container using a single
transaction and then recorded in `schema_migrations` as
`011_add_next_route_selection_indexes.sql`.

| Check | Result |
|---|---|
| Applied `011` after | `1` |
| Postgres restart count | `0` |
| Postgres health after | `running/healthy` |
| `pg_isready` after | `ready` |

## Verified Indexes

- `idx_deliveries_consumer_item_selected_at`
- `idx_deliveries_consumer_status_item`
- `idx_deliveries_item`
- `idx_deliveries_item_selected_at`
- `idx_entitlements_consumer_feature_status`
- `idx_quiz_items_cell_lookup`
- `idx_quiz_items_selection_pool`

Verified target index count: `7`.

## Log Notes

The migration itself completed with `CREATE INDEX` for all seven indexes,
`INSERT 0 1` for the migration record, and `COMMIT`.

Postgres logs include operator SQL syntax errors from failed verification
commands at `2026-06-12T05:39:05Z`, `2026-06-12T05:41:51Z`,
`2026-06-12T05:49:33Z`, and `2026-06-12T05:51:11Z`. These were quoting errors
in read/update verification commands and are documented as operator errors, not
runtime failures. Final log check after `2026-06-12T05:52:00Z` showed no API or
Postgres runtime errors.
