PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS scheduled_delivery_slots (
    slot_run_id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    consumer_id TEXT NOT NULL REFERENCES consumers(consumer_id),
    channel_id TEXT NOT NULL,
    delivery_date TEXT NOT NULL,
    slot_id TEXT NOT NULL,
    cefr_level TEXT NOT NULL,
    theme_id TEXT NOT NULL,
    delivery_id TEXT REFERENCES deliveries(delivery_id),
    status TEXT NOT NULL CHECK (
        status IN ('pending', 'created', 'sent', 'failed', 'skipped', 'no_item')
    ),
    failure_reason TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (
        consumer_id,
        channel_id,
        delivery_date,
        slot_id,
        theme_id,
        cefr_level
    )
);

CREATE INDEX IF NOT EXISTS idx_scheduled_delivery_slots_consumer_date
    ON scheduled_delivery_slots(consumer_id, delivery_date, status);
