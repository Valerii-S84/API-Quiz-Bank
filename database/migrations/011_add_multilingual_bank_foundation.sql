PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS languages (
    code TEXT PRIMARY KEY CHECK (code IN ('de', 'en', 'fr', 'es', 'nl')),
    name TEXT NOT NULL CHECK (name <> ''),
    is_active INTEGER NOT NULL CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS content_banks (
    id TEXT PRIMARY KEY,
    slug TEXT NOT NULL CHECK (slug <> ''),
    language_code TEXT NOT NULL REFERENCES languages(code),
    name TEXT NOT NULL CHECK (name <> ''),
    status TEXT NOT NULL CHECK (status IN ('draft', 'active', 'archived')),
    created_at TEXT NOT NULL,
    UNIQUE (language_code, slug)
);

CREATE TABLE IF NOT EXISTS content_bank_versions (
    id TEXT PRIMARY KEY,
    content_bank_id TEXT NOT NULL REFERENCES content_banks(id),
    version TEXT NOT NULL CHECK (version <> ''),
    status TEXT NOT NULL CHECK (status IN ('draft', 'audit', 'active', 'archived')),
    activated_at TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (content_bank_id, version)
);

CREATE TABLE IF NOT EXISTS content_bank_activation_events (
    activation_event_id TEXT PRIMARY KEY,
    content_bank_id TEXT NOT NULL REFERENCES content_banks(id),
    from_bank_version_id TEXT REFERENCES content_bank_versions(id),
    to_bank_version_id TEXT NOT NULL REFERENCES content_bank_versions(id),
    actor TEXT NOT NULL CHECK (actor <> ''),
    reason TEXT NOT NULL CHECK (reason <> ''),
    activated_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_content_bank_versions_one_active
    ON content_bank_versions(content_bank_id)
    WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_content_bank_versions_status
    ON content_bank_versions(content_bank_id, status, activated_at);

INSERT OR IGNORE INTO languages (code, name, is_active, created_at) VALUES
    ('de', 'German', 1, '2026-06-12T00:00:00Z'),
    ('en', 'English', 0, '2026-06-12T00:00:00Z'),
    ('fr', 'French', 0, '2026-06-12T00:00:00Z'),
    ('es', 'Spanish', 0, '2026-06-12T00:00:00Z'),
    ('nl', 'Dutch', 0, '2026-06-12T00:00:00Z');

INSERT OR IGNORE INTO content_banks (
    id, slug, language_code, name, status, created_at
) VALUES (
    'german-core',
    'german-core',
    'de',
    'German Core',
    'active',
    '2026-06-12T00:00:00Z'
);

INSERT OR IGNORE INTO content_bank_versions (
    id, content_bank_id, version, status, activated_at, created_at
) VALUES (
    'german-core:2026-06-12-baseline',
    'german-core',
    '2026-06-12-baseline',
    'active',
    '2026-06-12T00:00:00Z',
    '2026-06-12T00:00:00Z'
);

INSERT OR IGNORE INTO content_bank_activation_events (
    activation_event_id, content_bank_id, from_bank_version_id,
    to_bank_version_id, actor, reason, activated_at
) VALUES (
    'activation:german-core:2026-06-12-baseline',
    'german-core',
    NULL,
    'german-core:2026-06-12-baseline',
    'system_migration',
    'Baseline German content bank activation',
    '2026-06-12T00:00:00Z'
);
