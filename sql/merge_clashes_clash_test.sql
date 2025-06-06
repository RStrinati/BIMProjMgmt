-- MERGE for clashes_clash_test
WITH src_deduped AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY clash_test_id
        ORDER BY started_at DESC
    ) AS rn
    FROM staging.clashes_clash_test
    WHERE clash_test_id IS NOT NULL
)
MERGE INTO dbo.clashes_clash_test AS tgt
USING (SELECT * FROM src_deduped WHERE rn = 1) AS src
ON tgt.clash_test_id = src.clash_test_id
WHEN MATCHED THEN
    UPDATE SET
        bim360_account_id = src.bim360_account_id,
        bim360_project_id = src.bim360_project_id,
        model_set_id = src.model_set_id,
        model_set_version = src.model_set_version,
        root_folder_urn = src.root_folder_urn,
        started_at = src.started_at,
        completed_at = src.completed_at,
        status = src.status,
        backend_type = src.backend_type
WHEN NOT MATCHED THEN
    INSERT (clash_test_id, bim360_account_id, bim360_project_id, model_set_id, model_set_version,
            root_folder_urn, started_at, completed_at, status, backend_type)
    VALUES (src.clash_test_id, src.bim360_account_id, src.bim360_project_id, src.model_set_id, src.model_set_version,
            src.root_folder_urn, src.started_at, src.completed_at, src.status, src.backend_type);
