CREATE INDEX IF NOT EXISTS idx_quiz_items_selection_pool
    ON quiz_items(status, sublevel, theme_id, objective_id, pattern_id, item_id);

CREATE INDEX IF NOT EXISTS idx_quiz_items_cell_lookup
    ON quiz_items(theme_id, pattern_id, item_id);

CREATE INDEX IF NOT EXISTS idx_deliveries_item
    ON deliveries(quiz_item_id);

CREATE INDEX IF NOT EXISTS idx_deliveries_item_selected_at
    ON deliveries(quiz_item_id, selected_at DESC);

CREATE INDEX IF NOT EXISTS idx_deliveries_consumer_status_item
    ON deliveries(consumer_id, delivery_status, quiz_item_id);

CREATE INDEX IF NOT EXISTS idx_deliveries_consumer_item_selected_at
    ON deliveries(consumer_id, quiz_item_id, selected_at DESC);

CREATE INDEX IF NOT EXISTS idx_entitlements_consumer_feature_status
    ON entitlements(consumer_id, feature, status, valid_until, created_at);
