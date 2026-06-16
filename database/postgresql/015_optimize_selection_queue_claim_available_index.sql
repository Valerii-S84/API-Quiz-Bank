CREATE INDEX IF NOT EXISTS idx_selection_queue_items_available_claim
    ON selection_queue_items(queue_id, position, queue_item_id)
    INCLUDE (item_id)
    WHERE claim_status = 'available';
