PRAGMA foreign_keys = ON;

-- Stage 5 channel/tariff scope is applied by database_runtime.py.
-- SQLite migrations in this repository are replayed directly, so adaptive
-- column additions and quota_usage rebuilds must stay in the idempotent
-- runtime compatibility layer.
