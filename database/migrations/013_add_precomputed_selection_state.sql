PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS candidate_pools (
    pool_id TEXT PRIMARY KEY,
    language_code TEXT NOT NULL REFERENCES languages(code),
    content_bank_id TEXT NOT NULL REFERENCES content_banks(id),
    bank_version_id TEXT NOT NULL REFERENCES content_bank_versions(id),
    cefr_level TEXT NOT NULL DEFAULT '',
    theme_id TEXT NOT NULL DEFAULT '',
    objective_id TEXT NOT NULL DEFAULT '',
    pattern_id TEXT NOT NULL DEFAULT '',
    pool_status TEXT NOT NULL CHECK (
        pool_status IN ('building', 'ready', 'stale', 'disabled')
    ),
    pool_version INTEGER NOT NULL CHECK (pool_version >= 1),
    source_fingerprint TEXT NOT NULL CHECK (source_fingerprint <> ''),
    item_count INTEGER NOT NULL DEFAULT 0 CHECK (item_count >= 0),
    rebuilt_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (
        language_code,
        content_bank_id,
        bank_version_id,
        cefr_level,
        theme_id,
        objective_id,
        pattern_id,
        pool_version
    )
);

CREATE TABLE IF NOT EXISTS candidate_pool_items (
    pool_id TEXT NOT NULL REFERENCES candidate_pools(pool_id) ON DELETE CASCADE,
    item_id TEXT NOT NULL REFERENCES quiz_items(item_id),
    item_status TEXT NOT NULL CHECK (item_status IN ('approved', 'published')),
    rank_position INTEGER NOT NULL CHECK (rank_position >= 0),
    score_snapshot_json TEXT NOT NULL DEFAULT '{}' CHECK (score_snapshot_json <> ''),
    created_at TEXT NOT NULL,
    PRIMARY KEY (pool_id, item_id),
    UNIQUE (pool_id, rank_position)
);

CREATE TABLE IF NOT EXISTS consumer_delivery_state (
    consumer_id TEXT NOT NULL REFERENCES consumers(consumer_id),
    channel_id TEXT NOT NULL DEFAULT 'api' CHECK (channel_id <> ''),
    language_code TEXT NOT NULL REFERENCES languages(code),
    content_bank_id TEXT NOT NULL REFERENCES content_banks(id),
    bank_version_id TEXT NOT NULL REFERENCES content_bank_versions(id),
    quiz_item_id TEXT NOT NULL REFERENCES quiz_items(item_id),
    delivery_count INTEGER NOT NULL DEFAULT 0 CHECK (delivery_count >= 0),
    last_delivery_id TEXT REFERENCES deliveries(delivery_id),
    last_delivery_status TEXT NOT NULL DEFAULT '',
    last_delivered_at TEXT,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (
        consumer_id,
        channel_id,
        language_code,
        content_bank_id,
        bank_version_id,
        quiz_item_id
    )
);

CREATE TABLE IF NOT EXISTS selection_queues (
    queue_id TEXT PRIMARY KEY,
    consumer_id TEXT NOT NULL REFERENCES consumers(consumer_id),
    channel_id TEXT NOT NULL DEFAULT 'api' CHECK (channel_id <> ''),
    language_code TEXT NOT NULL REFERENCES languages(code),
    content_bank_id TEXT NOT NULL REFERENCES content_banks(id),
    bank_version_id TEXT NOT NULL REFERENCES content_bank_versions(id),
    cefr_level TEXT NOT NULL DEFAULT '',
    theme_id TEXT NOT NULL DEFAULT '',
    objective_id TEXT NOT NULL DEFAULT '',
    pattern_id TEXT NOT NULL DEFAULT '',
    queue_status TEXT NOT NULL CHECK (
        queue_status IN ('warming', 'ready', 'draining', 'disabled')
    ),
    target_size INTEGER NOT NULL CHECK (target_size > 0),
    available_count INTEGER NOT NULL DEFAULT 0 CHECK (available_count >= 0),
    refill_after_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (
        consumer_id,
        channel_id,
        language_code,
        content_bank_id,
        bank_version_id,
        cefr_level,
        theme_id,
        objective_id,
        pattern_id
    )
);

CREATE TABLE IF NOT EXISTS selection_queue_items (
    queue_item_id TEXT PRIMARY KEY,
    queue_id TEXT NOT NULL REFERENCES selection_queues(queue_id) ON DELETE CASCADE,
    pool_id TEXT REFERENCES candidate_pools(pool_id),
    item_id TEXT NOT NULL REFERENCES quiz_items(item_id),
    position INTEGER NOT NULL CHECK (position >= 0),
    claim_status TEXT NOT NULL CHECK (
        claim_status IN ('available', 'claimed', 'delivered', 'expired', 'skipped')
    ),
    claim_token TEXT,
    claimed_at TEXT,
    claim_expires_at TEXT,
    delivery_id TEXT REFERENCES deliveries(delivery_id),
    score_snapshot_json TEXT NOT NULL DEFAULT '{}' CHECK (score_snapshot_json <> ''),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (queue_id, position),
    UNIQUE (queue_id, item_id)
);

CREATE TABLE IF NOT EXISTS selection_diagnostic_events (
    event_id TEXT PRIMARY KEY,
    selection_request_id TEXT,
    consumer_id TEXT NOT NULL REFERENCES consumers(consumer_id),
    channel_id TEXT NOT NULL DEFAULT 'api' CHECK (channel_id <> ''),
    language_code TEXT NOT NULL REFERENCES languages(code),
    content_bank_id TEXT NOT NULL REFERENCES content_banks(id),
    bank_version_id TEXT NOT NULL REFERENCES content_bank_versions(id),
    event_type TEXT NOT NULL CHECK (
        event_type IN (
            'no_candidate',
            'queue_empty',
            'queue_refill',
            'selection_claim',
            'fallback_used',
            'diagnostic_snapshot'
        )
    ),
    reason_code TEXT NOT NULL DEFAULT '',
    payload_json TEXT NOT NULL DEFAULT '{}' CHECK (payload_json <> ''),
    occurred_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS selection_diagnostic_outbox (
    outbox_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL UNIQUE REFERENCES selection_diagnostic_events(event_id)
        ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (
        status IN ('pending', 'processing', 'published', 'failed', 'discarded')
    ),
    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    next_attempt_at TEXT,
    locked_at TEXT,
    locked_by TEXT,
    last_error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_candidate_pools_scope_ready
    ON candidate_pools(
        language_code,
        bank_version_id,
        pool_status,
        cefr_level,
        theme_id,
        objective_id,
        pattern_id
    );

CREATE INDEX IF NOT EXISTS idx_candidate_pool_items_pool_rank
    ON candidate_pool_items(pool_id, rank_position);

CREATE INDEX IF NOT EXISTS idx_candidate_pool_items_item
    ON candidate_pool_items(item_id);

CREATE INDEX IF NOT EXISTS idx_consumer_delivery_state_recent
    ON consumer_delivery_state(
        consumer_id,
        channel_id,
        language_code,
        bank_version_id,
        last_delivered_at DESC
    );

CREATE INDEX IF NOT EXISTS idx_selection_queues_scope_status
    ON selection_queues(
        consumer_id,
        channel_id,
        language_code,
        bank_version_id,
        queue_status
    );

CREATE INDEX IF NOT EXISTS idx_selection_queue_items_claim
    ON selection_queue_items(queue_id, claim_status, position, queue_item_id);

CREATE INDEX IF NOT EXISTS idx_selection_queue_items_item
    ON selection_queue_items(item_id);

CREATE INDEX IF NOT EXISTS idx_selection_diagnostic_events_consumer_created
    ON selection_diagnostic_events(consumer_id, language_code, bank_version_id, created_at);

CREATE INDEX IF NOT EXISTS idx_selection_diagnostic_outbox_pending
    ON selection_diagnostic_outbox(status, next_attempt_at, created_at)
    WHERE status IN ('pending', 'failed');
