-- MERGE for admin_project_user_roles
WITH src_deduped AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY project_id, user_id, role_id
        ORDER BY created_at DESC
    ) AS rn
    FROM staging.admin_project_user_roles
    WHERE project_id IS NOT NULL AND user_id IS NOT NULL AND role_id IS NOT NULL
)
MERGE INTO dbo.admin_project_user_roles AS tgt
USING (SELECT * FROM src_deduped WHERE rn = 1) AS src
ON tgt.project_id = src.project_id AND tgt.user_id = src.user_id AND tgt.role_id = src.role_id
WHEN MATCHED THEN
    UPDATE SET
        bim360_account_id = src.bim360_account_id,
        created_at = src.created_at
WHEN NOT MATCHED THEN
    INSERT (project_id, user_id, role_id, bim360_account_id, created_at)
    VALUES (src.project_id, src.user_id, src.role_id, src.bim360_account_id, src.created_at);
