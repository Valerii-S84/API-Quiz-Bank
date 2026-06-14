ALTER TABLE consumers
    ADD COLUMN IF NOT EXISTS default_language_code TEXT NOT NULL DEFAULT 'de' REFERENCES languages(code),
    ADD COLUMN IF NOT EXISTS default_content_bank_id TEXT NOT NULL DEFAULT 'german-core'
        REFERENCES content_banks(id),
    ADD COLUMN IF NOT EXISTS default_bank_version_id TEXT NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS allowed_language_codes_json TEXT NOT NULL DEFAULT '["de"]',
    ADD COLUMN IF NOT EXISTS allowed_content_bank_ids_json TEXT NOT NULL DEFAULT '["german-core"]',
    ADD COLUMN IF NOT EXISTS allowed_bank_version_ids_json TEXT NOT NULL DEFAULT '[]';

ALTER TABLE entitlements
    ADD COLUMN IF NOT EXISTS allowed_language_codes_json TEXT NOT NULL DEFAULT '["de"]',
    ADD COLUMN IF NOT EXISTS allowed_content_bank_ids_json TEXT NOT NULL DEFAULT '["german-core"]',
    ADD COLUMN IF NOT EXISTS allowed_bank_version_ids_json TEXT NOT NULL DEFAULT '[]',
    ADD COLUMN IF NOT EXISTS allowed_content_types_json TEXT NOT NULL DEFAULT '[]';

ALTER TABLE quota_usage
    ADD COLUMN IF NOT EXISTS language_code TEXT NOT NULL DEFAULT 'de' REFERENCES languages(code),
    ADD COLUMN IF NOT EXISTS content_bank_id TEXT NOT NULL DEFAULT 'german-core' REFERENCES content_banks(id),
    ADD COLUMN IF NOT EXISTS bank_version_id TEXT NOT NULL DEFAULT 'german-core:2026-06-12-baseline'
        REFERENCES content_bank_versions(id);

ALTER TABLE quota_usage
    DROP CONSTRAINT IF EXISTS quota_usage_consumer_id_feature_usage_date_key;

ALTER TABLE quota_usage
    DROP CONSTRAINT IF EXISTS quota_usage_content_scope_key;

ALTER TABLE quota_usage
    ADD CONSTRAINT quota_usage_content_scope_key UNIQUE (
        consumer_id,
        feature,
        usage_date,
        language_code,
        content_bank_id,
        bank_version_id
    );

ALTER TABLE scheduled_delivery_slots
    DROP CONSTRAINT IF EXISTS scheduled_delivery_slots_consumer_id_channel_id_delivery_date_slot_id_key;

ALTER TABLE scheduled_delivery_slots
    DROP CONSTRAINT IF EXISTS scheduled_delivery_slots_content_scope_key;

ALTER TABLE scheduled_delivery_slots
    ADD CONSTRAINT scheduled_delivery_slots_content_scope_key UNIQUE (
        consumer_id,
        channel_id,
        delivery_date,
        slot_id,
        language_code,
        content_bank_id,
        bank_version_id,
        theme_id,
        cefr_level
    );

CREATE INDEX IF NOT EXISTS idx_quota_usage_content_scope
    ON quota_usage(
        consumer_id,
        feature,
        usage_date,
        language_code,
        content_bank_id,
        bank_version_id
    );
