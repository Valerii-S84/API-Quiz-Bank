PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS quiz_item_image_quality_policy (
    item_id TEXT PRIMARY KEY REFERENCES quiz_items(item_id) ON DELETE CASCADE,
    theme_group TEXT NOT NULL CHECK (
        theme_group IN ('simple_visual', 'situational', 'abstract_complex')
    ),
    image_quality_recommended TEXT NOT NULL CHECK (
        image_quality_recommended IN ('low', 'medium')
    ),
    image_quality_source TEXT NOT NULL CHECK (
        image_quality_source IN ('policy', 'override')
    ),
    image_quality_policy_share INTEGER NOT NULL CHECK (
        image_quality_policy_share >= 0 AND image_quality_policy_share <= 70
    ),
    image_quality_override TEXT CHECK (
        image_quality_override IS NULL OR image_quality_override IN ('low', 'medium')
    ),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_quiz_item_image_quality_policy_group
    ON quiz_item_image_quality_policy(theme_group, image_quality_recommended);
