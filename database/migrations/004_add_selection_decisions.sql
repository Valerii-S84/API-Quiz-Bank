PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS selection_decisions (
    selection_request_id TEXT PRIMARY KEY,
    delivery_id TEXT REFERENCES deliveries(delivery_id) ON DELETE SET NULL,
    consumer_id TEXT NOT NULL REFERENCES consumers(consumer_id),
    delivery_mode TEXT NOT NULL,
    selection_strategy TEXT NOT NULL,
    filters_json TEXT NOT NULL,
    filters_applied_json TEXT NOT NULL,
    candidate_count INTEGER NOT NULL,
    eligible_count INTEGER NOT NULL,
    selected_item_id TEXT REFERENCES quiz_items(item_id),
    selected_score_json TEXT NOT NULL,
    selected_reason TEXT NOT NULL,
    blocked_reason_counts_json TEXT NOT NULL,
    fallback_reason_code TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_selection_decisions_consumer_created
    ON selection_decisions(consumer_id, created_at);

CREATE INDEX IF NOT EXISTS idx_selection_decisions_selected_item
    ON selection_decisions(selected_item_id);
