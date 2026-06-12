CREATE TABLE IF NOT EXISTS languages (
    code TEXT PRIMARY KEY CHECK (code IN ('de', 'en', 'fr', 'es', 'nl')),
    name TEXT NOT NULL CHECK (name <> ''),
    is_active BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS content_banks (
    id TEXT PRIMARY KEY,
    slug TEXT NOT NULL CHECK (slug <> ''),
    language_code TEXT NOT NULL REFERENCES languages(code),
    name TEXT NOT NULL CHECK (name <> ''),
    status TEXT NOT NULL CHECK (status IN ('draft', 'active', 'archived')),
    created_at TIMESTAMPTZ NOT NULL,
    UNIQUE (language_code, slug)
);

CREATE TABLE IF NOT EXISTS content_bank_versions (
    id TEXT PRIMARY KEY,
    content_bank_id TEXT NOT NULL REFERENCES content_banks(id),
    version TEXT NOT NULL CHECK (version <> ''),
    status TEXT NOT NULL CHECK (status IN ('draft', 'audit', 'active', 'archived')),
    activated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL,
    UNIQUE (content_bank_id, version)
);

CREATE TABLE IF NOT EXISTS content_bank_activation_events (
    activation_event_id TEXT PRIMARY KEY,
    content_bank_id TEXT NOT NULL REFERENCES content_banks(id),
    from_bank_version_id TEXT REFERENCES content_bank_versions(id),
    to_bank_version_id TEXT NOT NULL REFERENCES content_bank_versions(id),
    actor TEXT NOT NULL CHECK (actor <> ''),
    reason TEXT NOT NULL CHECK (reason <> ''),
    activated_at TIMESTAMPTZ NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_content_bank_versions_one_active
    ON content_bank_versions(content_bank_id)
    WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_content_bank_versions_status
    ON content_bank_versions(content_bank_id, status, activated_at);

INSERT INTO languages (code, name, is_active, created_at) VALUES
    ('de', 'German', TRUE, '2026-06-12T00:00:00Z'),
    ('en', 'English', FALSE, '2026-06-12T00:00:00Z'),
    ('fr', 'French', FALSE, '2026-06-12T00:00:00Z'),
    ('es', 'Spanish', FALSE, '2026-06-12T00:00:00Z'),
    ('nl', 'Dutch', FALSE, '2026-06-12T00:00:00Z')
ON CONFLICT (code) DO NOTHING;

INSERT INTO content_banks (
    id, slug, language_code, name, status, created_at
) VALUES (
    'german-core',
    'german-core',
    'de',
    'German Core',
    'active',
    '2026-06-12T00:00:00Z'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO content_bank_versions (
    id, content_bank_id, version, status, activated_at, created_at
) VALUES (
    'german-core:2026-06-12-baseline',
    'german-core',
    '2026-06-12-baseline',
    'active',
    '2026-06-12T00:00:00Z',
    '2026-06-12T00:00:00Z'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO content_bank_activation_events (
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
)
ON CONFLICT (activation_event_id) DO NOTHING;

ALTER TABLE sources
    ADD COLUMN IF NOT EXISTS language_code TEXT NOT NULL DEFAULT 'de' REFERENCES languages(code),
    ADD COLUMN IF NOT EXISTS content_bank_id TEXT NOT NULL DEFAULT 'german-core' REFERENCES content_banks(id),
    ADD COLUMN IF NOT EXISTS bank_version_id TEXT NOT NULL DEFAULT 'german-core:2026-06-12-baseline'
        REFERENCES content_bank_versions(id);

ALTER TABLE quiz_items
    ADD COLUMN IF NOT EXISTS language_code TEXT NOT NULL DEFAULT 'de' REFERENCES languages(code),
    ADD COLUMN IF NOT EXISTS content_bank_id TEXT NOT NULL DEFAULT 'german-core' REFERENCES content_banks(id),
    ADD COLUMN IF NOT EXISTS bank_version_id TEXT NOT NULL DEFAULT 'german-core:2026-06-12-baseline'
        REFERENCES content_bank_versions(id);

ALTER TABLE deliveries
    ADD COLUMN IF NOT EXISTS language_code TEXT NOT NULL DEFAULT 'de' REFERENCES languages(code),
    ADD COLUMN IF NOT EXISTS content_bank_id TEXT NOT NULL DEFAULT 'german-core' REFERENCES content_banks(id),
    ADD COLUMN IF NOT EXISTS bank_version_id TEXT NOT NULL DEFAULT 'german-core:2026-06-12-baseline'
        REFERENCES content_bank_versions(id);

ALTER TABLE selection_decisions
    ADD COLUMN IF NOT EXISTS language_code TEXT NOT NULL DEFAULT 'de' REFERENCES languages(code),
    ADD COLUMN IF NOT EXISTS content_bank_id TEXT NOT NULL DEFAULT 'german-core' REFERENCES content_banks(id),
    ADD COLUMN IF NOT EXISTS bank_version_id TEXT NOT NULL DEFAULT 'german-core:2026-06-12-baseline'
        REFERENCES content_bank_versions(id);

ALTER TABLE import_batches
    ADD COLUMN IF NOT EXISTS language_code TEXT NOT NULL DEFAULT 'de' REFERENCES languages(code),
    ADD COLUMN IF NOT EXISTS content_bank_id TEXT NOT NULL DEFAULT 'german-core' REFERENCES content_banks(id),
    ADD COLUMN IF NOT EXISTS bank_version_id TEXT NOT NULL DEFAULT 'german-core:2026-06-12-baseline'
        REFERENCES content_bank_versions(id);

ALTER TABLE import_batch_items
    ADD COLUMN IF NOT EXISTS language_code TEXT NOT NULL DEFAULT 'de' REFERENCES languages(code),
    ADD COLUMN IF NOT EXISTS content_bank_id TEXT NOT NULL DEFAULT 'german-core' REFERENCES content_banks(id),
    ADD COLUMN IF NOT EXISTS bank_version_id TEXT NOT NULL DEFAULT 'german-core:2026-06-12-baseline'
        REFERENCES content_bank_versions(id);

ALTER TABLE scheduled_delivery_slots
    ADD COLUMN IF NOT EXISTS language_code TEXT NOT NULL DEFAULT 'de' REFERENCES languages(code),
    ADD COLUMN IF NOT EXISTS content_bank_id TEXT NOT NULL DEFAULT 'german-core' REFERENCES content_banks(id),
    ADD COLUMN IF NOT EXISTS bank_version_id TEXT NOT NULL DEFAULT 'german-core:2026-06-12-baseline'
        REFERENCES content_bank_versions(id);

ALTER TABLE visual_assets
    ADD COLUMN IF NOT EXISTS language_code TEXT NOT NULL DEFAULT 'de' REFERENCES languages(code),
    ADD COLUMN IF NOT EXISTS content_bank_id TEXT NOT NULL DEFAULT 'german-core' REFERENCES content_banks(id),
    ADD COLUMN IF NOT EXISTS bank_version_id TEXT NOT NULL DEFAULT 'german-core:2026-06-12-baseline'
        REFERENCES content_bank_versions(id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_import_batch_items_bank_source_item
    ON import_batch_items(bank_version_id, source_id, source_item_id);

DROP INDEX IF EXISTS idx_quiz_items_selection_pool;
CREATE INDEX IF NOT EXISTS idx_quiz_items_selection_pool
    ON quiz_items(
        language_code,
        bank_version_id,
        status,
        sublevel,
        theme_id,
        objective_id,
        pattern_id,
        item_id
    );

DROP INDEX IF EXISTS idx_quiz_items_cell_lookup;
CREATE INDEX IF NOT EXISTS idx_quiz_items_cell_lookup
    ON quiz_items(language_code, bank_version_id, theme_id, pattern_id, item_id);

CREATE INDEX IF NOT EXISTS idx_deliveries_scope_item
    ON deliveries(
        consumer_id,
        language_code,
        bank_version_id,
        delivery_status,
        quiz_item_id
    );

CREATE INDEX IF NOT EXISTS idx_selection_decisions_scope_created
    ON selection_decisions(consumer_id, language_code, bank_version_id, created_at);
