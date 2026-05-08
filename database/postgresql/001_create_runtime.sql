CREATE TABLE sources (
    source_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    provenance_note TEXT NOT NULL,
    checksum_sha256 TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE quiz_items (
    item_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    language TEXT NOT NULL,
    level_band TEXT NOT NULL,
    sublevel TEXT NOT NULL,
    theme_id TEXT NOT NULL,
    subtheme_id TEXT NOT NULL,
    objective_id TEXT NOT NULL,
    pattern_id TEXT NOT NULL,
    difficulty_band TEXT NOT NULL,
    register TEXT NOT NULL,
    prompt TEXT NOT NULL,
    stem_text TEXT NOT NULL,
    options_json JSONB NOT NULL,
    answer_key TEXT NOT NULL,
    explanation TEXT NOT NULL,
    tags TEXT NOT NULL,
    coverage_cell_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN (
            'draft',
            'imported',
            'normalized',
            'needs_review',
            'approved',
            'published',
            'monitored',
            'retired',
            'blocked'
        )
    ),
    version TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    reviewed_at TIMESTAMPTZ,
    level_locked TEXT NOT NULL,
    locked_at TIMESTAMPTZ
);

CREATE TABLE consumers (
    consumer_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    allowed_cefr_levels_json JSONB NOT NULL,
    allowed_theme_ids_json JSONB NOT NULL,
    daily_quota_limit INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE api_credentials (
    credential_id TEXT PRIMARY KEY,
    consumer_id TEXT NOT NULL REFERENCES consumers(consumer_id),
    key_prefix TEXT NOT NULL,
    key_hash TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'suspended', 'revoked')),
    created_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    UNIQUE (consumer_id, key_prefix)
);

CREATE TABLE entitlements (
    entitlement_id TEXT PRIMARY KEY,
    consumer_id TEXT NOT NULL REFERENCES consumers(consumer_id),
    feature TEXT NOT NULL,
    status TEXT NOT NULL,
    allowed_cefr_levels_json JSONB NOT NULL,
    allowed_theme_ids_json JSONB NOT NULL,
    valid_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE quota_usage (
    quota_usage_id TEXT PRIMARY KEY,
    consumer_id TEXT NOT NULL REFERENCES consumers(consumer_id),
    feature TEXT NOT NULL,
    usage_date DATE NOT NULL,
    used_count INTEGER NOT NULL,
    quota_limit INTEGER NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    UNIQUE (consumer_id, feature, usage_date)
);

CREATE TABLE deliveries (
    delivery_id TEXT PRIMARY KEY,
    consumer_id TEXT NOT NULL REFERENCES consumers(consumer_id),
    quiz_item_id TEXT NOT NULL REFERENCES quiz_items(item_id),
    item_status TEXT NOT NULL CHECK (item_status IN ('approved', 'published')),
    delivery_status TEXT NOT NULL,
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    source_type TEXT NOT NULL,
    provenance_note TEXT NOT NULL,
    selection_reason_summary TEXT NOT NULL,
    selected_at TIMESTAMPTZ NOT NULL,
    entitlement_id TEXT NOT NULL REFERENCES entitlements(entitlement_id),
    quota_usage_id TEXT NOT NULL REFERENCES quota_usage(quota_usage_id)
);

CREATE TABLE audit_log (
    audit_id TEXT PRIMARY KEY,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    from_status TEXT NOT NULL,
    to_status TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_quiz_items_delivery_filter
    ON quiz_items(status, sublevel, theme_id, objective_id, pattern_id);

CREATE INDEX idx_deliveries_consumer_item
    ON deliveries(consumer_id, quiz_item_id);

CREATE INDEX idx_api_credentials_consumer_prefix
    ON api_credentials(consumer_id, key_prefix);
