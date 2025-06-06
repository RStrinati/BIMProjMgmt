-- MERGE for admin_project_user_services
WITH src_deduped AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY project_id, user_id, service
        ORDER BY created_at DESC
    ) AS rn
    FROM staging.admin_project_user_services
    WHERE project_id IS NOT NULL AND user_id IS NOT NULL AND service IS NOT NULL
)
MERGE INTO dbo.admin_project_user_services AS tgt
USING (SELECT * FROM src_deduped WHERE rn = 1) AS src
ON tgt.project_id = src.project_id AND tgt.user_id = src.user_id AND tgt.service = src.service
WHEN MATCHED THEN
    UPDATE SET
        bim360_account_id = src.bim360_account_id,
        role = src.role,
        created_at = src.created_at
WHEN NOT MATCHED THEN
    INSERT (project_id, user_id, service, bim360_account_id, role, created_at)
    VALUES (src.project_id, src.user_id, src.service, src.bim360_account_id, src.role, src.created_at);
