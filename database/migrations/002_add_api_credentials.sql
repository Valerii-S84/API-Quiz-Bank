CREATE TABLE IF NOT EXISTS api_credentials (
    credential_id TEXT PRIMARY KEY,
    consumer_id TEXT NOT NULL REFERENCES consumers(consumer_id),
    key_prefix TEXT NOT NULL,
    key_hash TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'suspended', 'revoked')),
    created_at TEXT NOT NULL,
    revoked_at TEXT,
    UNIQUE (consumer_id, key_prefix)
);

CREATE INDEX IF NOT EXISTS idx_api_credentials_consumer_prefix
    ON api_credentials(consumer_id, key_prefix);
