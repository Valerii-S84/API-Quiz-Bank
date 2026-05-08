CREATE TABLE import_batches (
    import_batch_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    parser_profile_id TEXT NOT NULL CHECK (parser_profile_id <> ''),
    import_mode TEXT NOT NULL CHECK (import_mode IN ('dry_run', 'commit')),
    import_status TEXT NOT NULL CHECK (
        import_status IN (
            'planned',
            'running',
            'dry_run_passed',
            'committed',
            'rejected',
            'failed',
            'rolled_back'
        )
    ),
    source_checksum_sha256 TEXT NOT NULL CHECK (
        source_checksum_sha256 ~ '^[0-9a-f]{64}$'
    ),
    default_item_status TEXT NOT NULL CHECK (
        default_item_status IN (
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
    row_count_detected INTEGER NOT NULL CHECK (row_count_detected >= 0),
    accepted_candidate_count INTEGER NOT NULL CHECK (accepted_candidate_count >= 0),
    rejected_candidate_count INTEGER NOT NULL CHECK (rejected_candidate_count >= 0),
    report_uri TEXT NOT NULL CHECK (report_uri <> ''),
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    created_by TEXT NOT NULL CHECK (created_by <> ''),
    UNIQUE (import_batch_id, source_id),
    CHECK (accepted_candidate_count + rejected_candidate_count <= row_count_detected),
    CHECK (
        (import_status IN ('running', 'planned') AND completed_at IS NULL)
        OR (import_status NOT IN ('running', 'planned') AND completed_at IS NOT NULL)
    )
);

CREATE TABLE import_batch_items (
    import_batch_id TEXT NOT NULL REFERENCES import_batches(import_batch_id),
    item_id TEXT NOT NULL REFERENCES quiz_items(item_id),
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    source_item_id TEXT NOT NULL CHECK (source_item_id <> ''),
    source_row_number INTEGER NOT NULL CHECK (source_row_number >= 1),
    canonical_status TEXT NOT NULL CHECK (
        canonical_status IN (
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
    content_hash_sha256 TEXT NOT NULL CHECK (
        content_hash_sha256 ~ '^[0-9a-f]{64}$'
    ),
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (import_batch_id, item_id),
    UNIQUE (import_batch_id, source_item_id),
    UNIQUE (item_id, content_hash_sha256),
    FOREIGN KEY (import_batch_id, source_id)
        REFERENCES import_batches(import_batch_id, source_id)
);

CREATE TABLE import_validation_results (
    validation_result_id TEXT PRIMARY KEY,
    import_batch_id TEXT NOT NULL REFERENCES import_batches(import_batch_id),
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    source_item_id TEXT,
    source_row_number INTEGER CHECK (source_row_number IS NULL OR source_row_number >= 1),
    severity TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'error')),
    rule_id TEXT NOT NULL CHECK (rule_id <> ''),
    message TEXT NOT NULL CHECK (message <> ''),
    created_at TIMESTAMPTZ NOT NULL,
    FOREIGN KEY (import_batch_id, source_id)
        REFERENCES import_batches(import_batch_id, source_id)
);

CREATE INDEX idx_import_batches_source_status
    ON import_batches(source_id, import_status, completed_at);

CREATE INDEX idx_import_batch_items_item
    ON import_batch_items(item_id);

CREATE INDEX idx_import_batch_items_source
    ON import_batch_items(source_id, source_item_id);

CREATE INDEX idx_import_validation_results_batch_severity
    ON import_validation_results(import_batch_id, severity);
