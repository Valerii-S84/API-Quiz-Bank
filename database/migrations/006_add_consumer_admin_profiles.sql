CREATE TABLE IF NOT EXISTS consumer_admin_profiles (
    consumer_id TEXT PRIMARY KEY REFERENCES consumers(consumer_id),
    display_name TEXT NOT NULL,
    consumer_kind TEXT NOT NULL CHECK (
        consumer_kind IN (
            'api_client',
            'telegram_channel',
            'telegram_bot',
            'teacher',
            'school'
        )
    ),
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_consumer_admin_profiles_kind
    ON consumer_admin_profiles(consumer_kind);
