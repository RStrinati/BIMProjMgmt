-- MERGE for admin_project_user_companies
WITH src_deduped AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY project_id, company_oxygen_id, user_id
        ORDER BY project_id
    ) AS rn
    FROM staging.admin_project_user_companies
    WHERE project_id IS NOT NULL AND company_oxygen_id IS NOT NULL AND user_id IS NOT NULL
)
MERGE INTO dbo.admin_project_user_companies AS tgt
USING (SELECT * FROM src_deduped WHERE rn = 1) AS src
ON tgt.project_id = src.project_id AND tgt.company_oxygen_id = src.company_oxygen_id AND tgt.user_id = src.user_id
WHEN MATCHED THEN
    UPDATE SET
        bim360_account_id = src.bim360_account_id
WHEN NOT MATCHED THEN
    INSERT (project_id, company_oxygen_id, user_id, bim360_account_id)
    VALUES (src.project_id, src.company_oxygen_id, src.user_id, src.bim360_account_id);
