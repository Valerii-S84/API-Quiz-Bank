PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS telegram_delivery_results (
    delivery_id TEXT PRIMARY KEY REFERENCES deliveries(delivery_id),
    consumer_id TEXT NOT NULL REFERENCES consumers(consumer_id),
    mode TEXT NOT NULL CHECK (mode IN ('dry_run', 'real')),
    status TEXT NOT NULL CHECK (status IN ('sent', 'failed', 'skipped')),
    telegram_target_ref TEXT NOT NULL,
    telegram_message_id TEXT,
    telegram_poll_id TEXT,
    failure_reason TEXT,
    recorded_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_telegram_delivery_results_consumer_status
    ON telegram_delivery_results(consumer_id, status, recorded_at);
