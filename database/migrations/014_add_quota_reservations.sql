PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS quota_reservations (
    quota_reservation_id TEXT PRIMARY KEY,
    quota_usage_id TEXT NOT NULL REFERENCES quota_usage(quota_usage_id) ON DELETE CASCADE,
    consumer_id TEXT NOT NULL REFERENCES consumers(consumer_id),
    feature TEXT NOT NULL,
    usage_date TEXT NOT NULL,
    language_code TEXT NOT NULL REFERENCES languages(code),
    content_bank_id TEXT NOT NULL REFERENCES content_banks(id),
    bank_version_id TEXT NOT NULL REFERENCES content_bank_versions(id),
    reservation_index INTEGER NOT NULL CHECK (reservation_index > 0),
    reservation_status TEXT NOT NULL CHECK (
        reservation_status IN ('available', 'claimed', 'finalized', 'expired')
    ),
    claim_token TEXT,
    claimed_at TEXT,
    finalized_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (
        consumer_id,
        feature,
        usage_date,
        language_code,
        content_bank_id,
        bank_version_id,
        reservation_index
    )
);

CREATE INDEX IF NOT EXISTS idx_quota_reservations_available_claim
    ON quota_reservations(
        consumer_id,
        feature,
        usage_date,
        language_code,
        content_bank_id,
        bank_version_id,
        reservation_status,
        reservation_index,
        quota_reservation_id
    );

CREATE INDEX IF NOT EXISTS idx_quota_reservations_finalized_scope
    ON quota_reservations(
        consumer_id,
        feature,
        usage_date,
        language_code,
        content_bank_id,
        bank_version_id,
        reservation_status
    );
