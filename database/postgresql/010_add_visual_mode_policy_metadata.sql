ALTER TABLE visual_assets
    ADD COLUMN IF NOT EXISTS visual_mode TEXT NOT NULL DEFAULT 'target_object' CHECK (
        visual_mode IN (
            'target_action',
            'target_object',
            'context_only',
            'document_form',
            'symbolic_abstract'
        )
    ),
    ADD COLUMN IF NOT EXISTS visual_target TEXT NOT NULL DEFAULT 'unknown' CHECK (visual_target <> ''),
    ADD COLUMN IF NOT EXISTS visual_context_hint TEXT NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS visual_prompt_policy_version TEXT NOT NULL DEFAULT 'unknown' CHECK (
        visual_prompt_policy_version <> ''
    );

ALTER TABLE visual_prompt_audit
    ADD COLUMN IF NOT EXISTS visual_mode TEXT NOT NULL DEFAULT 'target_object' CHECK (
        visual_mode IN (
            'target_action',
            'target_object',
            'context_only',
            'document_form',
            'symbolic_abstract'
        )
    ),
    ADD COLUMN IF NOT EXISTS visual_target TEXT NOT NULL DEFAULT 'unknown' CHECK (visual_target <> ''),
    ADD COLUMN IF NOT EXISTS visual_context_hint TEXT NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS visual_prompt_policy_version TEXT NOT NULL DEFAULT 'unknown' CHECK (
        visual_prompt_policy_version <> ''
    );
