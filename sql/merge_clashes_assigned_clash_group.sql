-- MERGE for clashes_assigned_clash_group
WITH src_deduped AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY clash_group_id
        ORDER BY created_at DESC
    ) AS rn
    FROM staging.clashes_assigned_clash_group
    WHERE clash_group_id IS NOT NULL
)
MERGE INTO dbo.clashes_assigned_clash_group AS tgt
USING (SELECT * FROM src_deduped WHERE rn = 1) AS src
ON tgt.clash_group_id = src.clash_group_id
WHEN MATCHED THEN
    UPDATE SET
        bim360_account_id = src.bim360_account_id,
        bim360_project_id = src.bim360_project_id,
        issue_id = src.issue_id,
        title = src.title,
        description = src.description,
        status = src.status,
        clash_test_id = src.clash_test_id,
        model_set_id = src.model_set_id,
        created_at_model_set_version = src.created_at_model_set_version,
        created_at = src.created_at,
        created_by = src.created_by
WHEN NOT MATCHED THEN
    INSERT (clash_group_id, bim360_account_id, bim360_project_id, issue_id, title, description, status,
            clash_test_id, model_set_id, created_at_model_set_version, created_at, created_by)
    VALUES (src.clash_group_id, src.bim360_account_id, src.bim360_project_id, src.issue_id, src.title, src.description, src.status,
            src.clash_test_id, src.model_set_id, src.created_at_model_set_version, src.created_at, src.created_by);
