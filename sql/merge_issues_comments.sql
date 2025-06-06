WITH src_deduped AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY comment_id
        ORDER BY created_at DESC
    ) AS rn
    FROM staging.issues_comments
    WHERE comment_id IS NOT NULL
)
MERGE INTO dbo.issues_comments AS tgt
USING (SELECT * FROM src_deduped WHERE rn = 1) AS src
ON tgt.comment_id = src.comment_id
WHEN MATCHED THEN
    UPDATE SET
        issue_id = src.issue_id,
        comment_body = src.comment_body,
        created_by = src.created_by,
        created_at = src.created_at,
        bim360_account_id = src.bim360_account_id,
        bim360_project_id = src.bim360_project_id,
        updated_at = GETDATE()
WHEN NOT MATCHED THEN
    INSERT (
        comment_id, bim360_account_id, bim360_project_id,
        issue_id, comment_body, created_by, created_at, updated_at
    )
    VALUES (
        src.comment_id, src.bim360_account_id, src.bim360_project_id,
        src.issue_id, src.comment_body, src.created_by, src.created_at, GETDATE()
    );
