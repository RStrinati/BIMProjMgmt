-- MERGE for issues_root_causes
WITH src_deduped AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY root_cause_id, bim360_account_id, bim360_project_id
        ORDER BY updated_at DESC
    ) AS rn
    FROM staging.issues_root_causes
)
MERGE INTO dbo.issues_root_causes AS tgt
USING (SELECT * FROM src_deduped WHERE rn = 1) AS src
ON tgt.root_cause_id = src.root_cause_id
   AND tgt.bim360_account_id = src.bim360_account_id
   AND tgt.bim360_project_id = src.bim360_project_id
WHEN MATCHED THEN
    UPDATE SET
        tgt.title = src.title,
        tgt.root_cause_category_id = src.root_cause_category_id,
        tgt.is_active = src.is_active,
        tgt.is_system = src.is_system,
        tgt.created_by = src.created_by,
        tgt.created_at = src.created_at,
        tgt.updated_by = src.updated_by,
        tgt.updated_at = src.updated_at,
        tgt.deleted_by = src.deleted_by,
        tgt.deleted_at = src.deleted_at
WHEN NOT MATCHED BY TARGET THEN
    INSERT (
        root_cause_id, bim360_account_id, bim360_project_id,
        root_cause_category_id, title, is_active, is_system,
        created_by, created_at, updated_by, updated_at,
        deleted_by, deleted_at
    )
    VALUES (
        src.root_cause_id, src.bim360_account_id, src.bim360_project_id,
        src.root_cause_category_id, src.title, src.is_active, src.is_system,
        src.created_by, src.created_at, src.updated_by, src.updated_at,
        src.deleted_by, src.deleted_at
    );
