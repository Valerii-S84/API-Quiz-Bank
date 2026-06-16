"""SQL templates for the PostgreSQL queue-first hot path."""

from __future__ import annotations


POSTGRESQL_CLAIM_ITEM_SQL_TEMPLATE = """
        WITH candidate AS (
            SELECT sqi.queue_item_id
            FROM selection_queue_items sqi
            JOIN selection_queues sq ON sq.queue_id = sqi.queue_id
            WHERE sqi.queue_id IN ({queue_placeholders})
              AND sq.queue_status IN ('ready', 'draining')
              AND sqi.claim_status = 'available'
              {excluded_clause}
            ORDER BY sqi.position ASC, sqi.queue_item_id ASC
            LIMIT 1
            FOR UPDATE OF sqi SKIP LOCKED
        ),
        updated AS (
            UPDATE selection_queue_items sqi
            SET claim_status = 'claimed',
                claim_token = ?,
                claimed_at = ?,
                claim_expires_at = NULL,
                updated_at = ?
            FROM candidate
            WHERE sqi.queue_item_id = candidate.queue_item_id
              AND sqi.claim_status = 'available'
            RETURNING sqi.queue_item_id, sqi.queue_id, sqi.item_id, sqi.score_snapshot_json
        )
        SELECT updated.queue_item_id, updated.queue_id, updated.score_snapshot_json,
               qi.*, s.source_type AS resolved_source_type,
               s.provenance_note AS resolved_provenance_note,
               iq.theme_group, iq.image_quality_recommended,
               iq.image_quality_source, iq.image_quality_policy_share,
               iq.image_quality_override
        FROM updated
        JOIN selection_queues sq ON sq.queue_id = updated.queue_id
        JOIN quiz_items qi ON qi.item_id = updated.item_id
        JOIN sources s ON s.source_id = qi.source_id
        LEFT JOIN quiz_item_image_quality_policy iq ON iq.item_id = qi.item_id
        WHERE qi.status IN ({status_placeholders})
          AND qi.language_code = sq.language_code
          AND qi.content_bank_id = sq.content_bank_id
          AND qi.bank_version_id = sq.bank_version_id
          AND (sq.cefr_level = '' OR qi.sublevel = sq.cefr_level)
          AND (sq.theme_id = '' OR qi.theme_id = sq.theme_id)
          AND (sq.objective_id = '' OR qi.objective_id = sq.objective_id)
          AND (sq.pattern_id = '' OR qi.pattern_id = sq.pattern_id)
          AND qi.source_id <> ''
          AND s.source_type <> ''
          AND s.provenance_note <> ''
    """
