CREATE TABLE telegram_delivery_results (
    delivery_id TEXT PRIMARY KEY REFERENCES deliveries(delivery_id),
    consumer_id TEXT NOT NULL REFERENCES consumers(consumer_id),
    mode TEXT NOT NULL CHECK (mode IN ('dry_run', 'real')),
    status TEXT NOT NULL CHECK (status IN ('sent', 'failed', 'skipped')),
    telegram_target_ref TEXT NOT NULL,
    telegram_message_id TEXT,
    telegram_poll_id TEXT,
    failure_reason TEXT,
    recorded_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_telegram_delivery_results_consumer_status
    ON telegram_delivery_results(consumer_id, status, recorded_at);

CREATE TABLE selection_decisions (
    selection_request_id TEXT PRIMARY KEY,
    delivery_id TEXT REFERENCES deliveries(delivery_id) ON DELETE SET NULL,
    consumer_id TEXT NOT NULL REFERENCES consumers(consumer_id),
    delivery_mode TEXT NOT NULL,
    selection_strategy TEXT NOT NULL,
    filters_json JSONB NOT NULL,
    filters_applied_json JSONB NOT NULL,
    candidate_count INTEGER NOT NULL,
    eligible_count INTEGER NOT NULL,
    selected_item_id TEXT REFERENCES quiz_items(item_id),
    selected_score_json JSONB NOT NULL,
    selected_reason TEXT NOT NULL,
    blocked_reason_counts_json JSONB NOT NULL,
    fallback_reason_code TEXT,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_selection_decisions_consumer_created
    ON selection_decisions(consumer_id, created_at);

CREATE INDEX idx_selection_decisions_selected_item
    ON selection_decisions(selected_item_id);
