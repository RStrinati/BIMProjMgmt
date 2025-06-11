-- MERGE for locations_nodes
WITH src_deduped AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY id
        ORDER BY updated_at DESC
    ) AS rn
    FROM staging.locations_nodes
    WHERE id IS NOT NULL
)
MERGE INTO dbo.locations_nodes AS tgt
USING (SELECT * FROM src_deduped WHERE rn = 1) AS src
ON tgt.id = src.id
WHEN MATCHED THEN
    UPDATE SET
        tree_id = src.tree_id,
        bim360_account_id = src.bim360_account_id,
        bim360_project_id = src.bim360_project_id,
        parent_id = src.parent_id,
        name = src.name,
        [order] = src.[order],
        created_at = src.created_at,
        updated_at = src.updated_at
WHEN NOT MATCHED THEN
    INSERT (id, tree_id, bim360_account_id, bim360_project_id, parent_id, name, [order], created_at, updated_at)
    VALUES (src.id, src.tree_id, src.bim360_account_id, src.bim360_project_id, src.parent_id, src.name, src.[order], src.created_at, src.updated_at);
