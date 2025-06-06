-- MERGE for admin_project_user_products
WITH src_deduped AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY bim360_project_id, user_id, product_key
        ORDER BY created_at DESC
    ) AS rn
    FROM staging.admin_project_user_products
    WHERE bim360_project_id IS NOT NULL AND user_id IS NOT NULL AND product_key IS NOT NULL
)
MERGE INTO dbo.admin_project_user_products AS tgt
USING (SELECT * FROM src_deduped WHERE rn = 1) AS src
ON tgt.bim360_project_id = src.bim360_project_id AND tgt.user_id = src.user_id AND tgt.product_key = src.product_key
WHEN MATCHED THEN
    UPDATE SET
        bim360_account_id = src.bim360_account_id,
        access_level = src.access_level,
        created_at = src.created_at
WHEN NOT MATCHED THEN
    INSERT (bim360_project_id, user_id, product_key, bim360_account_id, access_level, created_at)
    VALUES (src.bim360_project_id, src.user_id, src.product_key, src.bim360_account_id, src.access_level, src.created_at);
