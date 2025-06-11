-- MERGE for locations_trees
WITH src_deduped AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY id
        ORDER BY updated_at DESC
    ) AS rn
    FROM staging.locations_trees
    WHERE id IS NOT NULL
)
MERGE INTO dbo.locations_trees AS tgt
USING (SELECT * FROM src_deduped WHERE rn = 1) AS src
ON tgt.id = src.id
WHEN MATCHED THEN
    UPDATE SET
        bim360_account_id = src.bim360_account_id,
        bim360_project_id = src.bim360_project_id,
        name = src.name,
        created_at = src.created_at,
        updated_at = src.updated_at
WHEN NOT MATCHED THEN
    INSERT (id, bim360_account_id, bim360_project_id, name, created_at, updated_at)
    VALUES (src.id, src.bim360_account_id, src.bim360_project_id, src.name, src.created_at, src.updated_at);
