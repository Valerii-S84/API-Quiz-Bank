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
    claimed_at TIMESTAMPTZ,
    finalized_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
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

ALTER TABLE deliveries
    ADD COLUMN IF NOT EXISTS quota_reservation_id TEXT
    REFERENCES quota_reservations(quota_reservation_id);

CREATE INDEX IF NOT EXISTS idx_quota_reservations_available_claim
    ON quota_reservations(
        consumer_id,
        feature,
        usage_date,
        language_code,
        content_bank_id,
        bank_version_id,
        reservation_index,
        quota_reservation_id
    )
    INCLUDE (quota_usage_id)
    WHERE reservation_status = 'available';

CREATE INDEX IF NOT EXISTS idx_quota_reservations_finalized_scope
    ON quota_reservations(
        consumer_id,
        feature,
        usage_date,
        language_code,
        content_bank_id,
        bank_version_id
    )
    WHERE reservation_status IN ('claimed', 'finalized');

CREATE UNIQUE INDEX IF NOT EXISTS uq_deliveries_quota_reservation
    ON deliveries(quota_reservation_id)
    WHERE quota_reservation_id IS NOT NULL;
