-- MERGE for clashes_clash_group_to_clash_id
WITH src_deduped AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY clash_group_id, clash_id
        ORDER BY clash_id
    ) AS rn
    FROM staging.clashes_clash_group_to_clash_id
    WHERE clash_group_id IS NOT NULL AND clash_id IS NOT NULL
)
MERGE INTO dbo.clashes_clash_group_to_clash_id AS tgt
USING (SELECT * FROM src_deduped WHERE rn = 1) AS src
ON tgt.clash_group_id = src.clash_group_id AND tgt.clash_id = src.clash_id
WHEN MATCHED THEN
    UPDATE SET
        bim360_account_id = src.bim360_account_id,
        bim360_project_id = src.bim360_project_id
WHEN NOT MATCHED THEN
    INSERT (clash_group_id, clash_id, bim360_account_id, bim360_project_id)
    VALUES (src.clash_group_id, src.clash_id, src.bim360_account_id, src.bim360_project_id);
