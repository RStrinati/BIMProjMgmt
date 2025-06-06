-- MERGE for admin_project_roles
WITH src_deduped AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY bim360_project_id, role_oxygen_id
        ORDER BY bim360_project_id
    ) AS rn
    FROM staging.admin_project_roles
    WHERE bim360_project_id IS NOT NULL AND role_oxygen_id IS NOT NULL
)
MERGE INTO dbo.admin_project_roles AS tgt
USING (SELECT * FROM src_deduped WHERE rn = 1) AS src
ON tgt.bim360_project_id = src.bim360_project_id AND tgt.role_oxygen_id = src.role_oxygen_id
WHEN MATCHED THEN
    UPDATE SET
        bim360_account_id = src.bim360_account_id,
        name = src.name,
        status = src.status
WHEN NOT MATCHED THEN
    INSERT (bim360_project_id, role_oxygen_id, bim360_account_id, name, status)
    VALUES (src.bim360_project_id, src.role_oxygen_id, src.bim360_account_id, src.name, src.status);
