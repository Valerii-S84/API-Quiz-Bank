CREATE TABLE IF NOT EXISTS admin_credentials (
    credential_id TEXT PRIMARY KEY,
    actor TEXT NOT NULL,
    role TEXT NOT NULL CHECK (
        role IN ('owner', 'content_admin', 'read_only_reviewer')
    ),
    key_prefix TEXT NOT NULL,
    key_hash TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'suspended', 'revoked')),
    created_at TEXT NOT NULL,
    revoked_at TEXT,
    UNIQUE (actor, key_prefix)
);

CREATE INDEX IF NOT EXISTS idx_admin_credentials_actor_prefix
    ON admin_credentials(actor, key_prefix);
