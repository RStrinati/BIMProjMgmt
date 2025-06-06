-- MERGE for issues_root_cause_categories
WITH src_deduped AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY root_cause_category_id
        ORDER BY updated_at DESC
    ) AS rn
    FROM staging.issues_root_cause_categories
    WHERE root_cause_category_id IS NOT NULL
)
MERGE INTO dbo.issues_root_cause_categories AS tgt
USING (SELECT * FROM src_deduped WHERE rn = 1) AS src
ON tgt.root_cause_category_id = src.root_cause_category_id
WHEN MATCHED THEN
    UPDATE SET
        root_cause_category = src.root_cause_category,
        is_active = src.is_active,
        is_system = src.is_system,
        created_by = src.created_by,
        created_at = src.created_at,
        updated_by = src.updated_by,
        updated_at = src.updated_at,
        deleted_by = src.deleted_by,
        deleted_at = src.deleted_at
WHEN NOT MATCHED THEN
    INSERT (root_cause_category_id, root_cause_category, is_active, is_system,
            created_by, created_at, updated_by, updated_at, deleted_by, deleted_at)
    VALUES (src.root_cause_category_id, src.root_cause_category, src.is_active, src.is_system,
            src.created_by, src.created_at, src.updated_by, src.updated_at, src.deleted_by, src.deleted_at);
