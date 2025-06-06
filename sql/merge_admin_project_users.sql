-- MERGE for admin_project_users
WITH src_deduped AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY bim360_project_id, user_id
        ORDER BY updated_at DESC
    ) AS rn
    FROM staging.admin_project_users
    WHERE bim360_project_id IS NOT NULL AND user_id IS NOT NULL
)
MERGE INTO dbo.admin_project_users AS tgt
USING (SELECT * FROM src_deduped WHERE rn = 1) AS src
ON tgt.bim360_project_id = src.bim360_project_id AND tgt.user_id = src.user_id
WHEN MATCHED THEN
    UPDATE SET
        bim360_account_id = src.bim360_account_id,
        status = src.status,
        company_id = src.company_id,
        access_level = src.access_level,
        created_at = src.created_at,
        updated_at = src.updated_at
WHEN NOT MATCHED THEN
    INSERT (bim360_project_id, user_id, bim360_account_id, status, company_id,
            access_level, created_at, updated_at)
    VALUES (src.bim360_project_id, src.user_id, src.bim360_account_id, src.status, src.company_id,
            src.access_level, src.created_at, src.updated_at);
