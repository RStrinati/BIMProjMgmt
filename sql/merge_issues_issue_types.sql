-- MERGE for issues_issue_types
WITH src_deduped AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY issue_type_id
        ORDER BY updated_at DESC
    ) AS rn
    FROM staging.issues_issue_types
    WHERE issue_type_id IS NOT NULL
)
MERGE INTO dbo.issues_issue_types AS tgt
USING (SELECT * FROM src_deduped WHERE rn = 1) AS src
ON tgt.issue_type_id = src.issue_type_id
WHEN MATCHED THEN
    UPDATE SET
        bim360_account_id = src.bim360_account_id,
        bim360_project_id = src.bim360_project_id,
        issue_type = src.issue_type,
        is_active = src.is_active,
        created_by = src.created_by,
        created_at = src.created_at,
        updated_by = src.updated_by,
        updated_at = src.updated_at,
        deleted_by = src.deleted_by,
        deleted_at = src.deleted_at
WHEN NOT MATCHED THEN
    INSERT (issue_type_id, bim360_account_id, bim360_project_id, issue_type, is_active, created_by, created_at, updated_by, updated_at, deleted_by, deleted_at)
    VALUES (src.issue_type_id, src.bim360_account_id, src.bim360_project_id, src.issue_type, src.is_active, src.created_by, src.created_at, src.updated_by, src.updated_at, src.deleted_by, src.deleted_at);
