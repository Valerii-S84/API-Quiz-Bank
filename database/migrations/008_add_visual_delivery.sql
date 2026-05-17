PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS consumer_visual_settings (
    consumer_id TEXT PRIMARY KEY REFERENCES consumers(consumer_id),
    delivery_mode TEXT NOT NULL CHECK (
        delivery_mode IN ('text_only', 'image_standard', 'image_branded')
    ),
    visual_style TEXT NOT NULL CHECK (visual_style <> ''),
    branding_preset TEXT NOT NULL CHECK (branding_preset <> ''),
    fallback_policy TEXT NOT NULL CHECK (
        fallback_policy IN ('text_only', 'cache_only', 'block_visual_delivery')
    ),
    daily_visual_delivery_limit INTEGER NOT NULL CHECK (daily_visual_delivery_limit >= 0),
    daily_generation_limit INTEGER NOT NULL CHECK (daily_generation_limit >= 0),
    monthly_generation_limit INTEGER NOT NULL CHECK (monthly_generation_limit >= 0),
    is_active INTEGER NOT NULL CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS visual_assets (
    asset_id TEXT PRIMARY KEY,
    quiz_item_id TEXT NOT NULL REFERENCES quiz_items(item_id),
    consumer_id TEXT REFERENCES consumers(consumer_id),
    delivery_mode TEXT NOT NULL CHECK (
        delivery_mode IN ('text_only', 'image_standard', 'image_branded')
    ),
    visual_style TEXT NOT NULL CHECK (visual_style <> ''),
    branding_preset TEXT NOT NULL CHECK (branding_preset <> ''),
    image_version TEXT NOT NULL CHECK (image_version <> ''),
    language TEXT NOT NULL CHECK (language <> ''),
    cache_key TEXT NOT NULL UNIQUE CHECK (cache_key <> ''),
    image_path TEXT NOT NULL CHECK (image_path <> ''),
    image_sha256 TEXT NOT NULL CHECK (image_sha256 <> ''),
    mime_type TEXT NOT NULL CHECK (
        mime_type IN ('image/png', 'image/webp', 'image/jpeg')
    ),
    width INTEGER NOT NULL CHECK (width > 0),
    height INTEGER NOT NULL CHECK (height > 0),
    qa_status TEXT NOT NULL CHECK (
        qa_status IN ('approved', 'rejected', 'fallback_used', 'needs_review')
    ),
    provider_name TEXT NOT NULL CHECK (provider_name <> ''),
    provider_model TEXT NOT NULL CHECK (provider_model <> ''),
    provider_asset_ref TEXT,
    visual_mode TEXT NOT NULL DEFAULT 'target_object' CHECK (
        visual_mode IN (
            'target_action',
            'target_object',
            'context_only',
            'document_form',
            'symbolic_abstract'
        )
    ),
    visual_target TEXT NOT NULL DEFAULT 'unknown' CHECK (visual_target <> ''),
    visual_context_hint TEXT NOT NULL DEFAULT '',
    visual_prompt_policy_version TEXT NOT NULL DEFAULT 'unknown' CHECK (
        visual_prompt_policy_version <> ''
    ),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS visual_prompt_audit (
    prompt_id TEXT PRIMARY KEY,
    asset_id TEXT REFERENCES visual_assets(asset_id),
    quiz_item_id TEXT NOT NULL REFERENCES quiz_items(item_id),
    consumer_id TEXT REFERENCES consumers(consumer_id),
    prompt_type TEXT NOT NULL CHECK (prompt_type <> ''),
    visual_mode TEXT NOT NULL DEFAULT 'target_object' CHECK (
        visual_mode IN (
            'target_action',
            'target_object',
            'context_only',
            'document_form',
            'symbolic_abstract'
        )
    ),
    visual_target TEXT NOT NULL DEFAULT 'unknown' CHECK (visual_target <> ''),
    visual_context_hint TEXT NOT NULL DEFAULT '',
    generated_prompt TEXT NOT NULL CHECK (generated_prompt <> ''),
    negative_prompt TEXT NOT NULL,
    prompt_policy_version TEXT NOT NULL CHECK (prompt_policy_version <> ''),
    visual_prompt_policy_version TEXT NOT NULL DEFAULT 'unknown' CHECK (
        visual_prompt_policy_version <> ''
    ),
    provider_name TEXT NOT NULL CHECK (provider_name <> ''),
    provider_model TEXT NOT NULL CHECK (provider_model <> ''),
    provider_response_id TEXT,
    provider_revised_prompt TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS visual_delivery_results (
    delivery_id TEXT PRIMARY KEY REFERENCES deliveries(delivery_id),
    consumer_id TEXT NOT NULL REFERENCES consumers(consumer_id),
    asset_id TEXT REFERENCES visual_assets(asset_id),
    requested_delivery_mode TEXT NOT NULL CHECK (
        requested_delivery_mode IN ('text_only', 'image_standard', 'image_branded')
    ),
    resolved_delivery_mode TEXT NOT NULL CHECK (
        resolved_delivery_mode IN ('text_only', 'image_standard', 'image_branded')
    ),
    visual_status TEXT NOT NULL CHECK (
        visual_status IN ('sent', 'skipped', 'failed', 'fallback_used')
    ),
    fallback_used INTEGER NOT NULL CHECK (fallback_used IN (0, 1)),
    fallback_reason TEXT,
    telegram_image_message_id TEXT,
    recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS visual_usage_events (
    usage_event_id TEXT PRIMARY KEY,
    consumer_id TEXT NOT NULL REFERENCES consumers(consumer_id),
    delivery_id TEXT REFERENCES deliveries(delivery_id),
    asset_id TEXT REFERENCES visual_assets(asset_id),
    event_type TEXT NOT NULL CHECK (
        event_type IN (
            'cache_hit',
            'cache_miss',
            'generation_requested',
            'generation_succeeded',
            'generation_failed',
            'qa_approved',
            'qa_rejected',
            'fallback_used'
        )
    ),
    feature TEXT NOT NULL CHECK (feature <> ''),
    quantity INTEGER NOT NULL CHECK (quantity >= 0),
    estimated_cost_minor INTEGER NOT NULL CHECK (estimated_cost_minor >= 0),
    provider_name TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_consumer_visual_settings_mode
    ON consumer_visual_settings(delivery_mode, is_active);

CREATE INDEX IF NOT EXISTS idx_visual_assets_quiz_consumer
    ON visual_assets(quiz_item_id, consumer_id, qa_status);

CREATE INDEX IF NOT EXISTS idx_visual_prompt_audit_item_created
    ON visual_prompt_audit(quiz_item_id, created_at);

CREATE INDEX IF NOT EXISTS idx_visual_delivery_results_consumer_status
    ON visual_delivery_results(consumer_id, visual_status, recorded_at);

CREATE INDEX IF NOT EXISTS idx_visual_usage_events_consumer_feature
    ON visual_usage_events(consumer_id, feature, created_at);
