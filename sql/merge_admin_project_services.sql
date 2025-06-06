-- MERGE for admin_project_services
WITH src_deduped AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY project_id, service
        ORDER BY created_at DESC
    ) AS rn
    FROM staging.admin_project_services
    WHERE project_id IS NOT NULL AND service IS NOT NULL
)
MERGE INTO dbo.admin_project_services AS tgt
USING (SELECT * FROM src_deduped WHERE rn = 1) AS src
ON tgt.project_id = src.project_id AND tgt.service = src.service
WHEN MATCHED THEN
    UPDATE SET
        bim360_account_id = src.bim360_account_id,
        status = src.status,
        created_at = src.created_at
WHEN NOT MATCHED THEN
    INSERT (project_id, service, bim360_account_id, status, created_at)
    VALUES (src.project_id, src.service, src.bim360_account_id, src.status, src.created_at);
