-- MERGE for admin_roles
WITH src_deduped AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY id
        ORDER BY id
    ) AS rn
    FROM staging.admin_roles
    WHERE id IS NOT NULL
)
MERGE INTO dbo.admin_roles AS tgt
USING (SELECT * FROM src_deduped WHERE rn = 1) AS src
ON tgt.id = src.id
WHEN MATCHED THEN
    UPDATE SET
        bim360_account_id = src.bim360_account_id,
        name = src.name,
        status = src.status
WHEN NOT MATCHED THEN
    INSERT (id, bim360_account_id, name, status)
    VALUES (src.id, src.bim360_account_id, src.name, src.status);
