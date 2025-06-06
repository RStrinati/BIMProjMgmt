-- MERGE for issues_attachments
WITH src_deduped AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY attachment_id
        ORDER BY updated_at DESC
    ) AS rn
    FROM staging.issues_attachments
    WHERE attachment_id IS NOT NULL
)
MERGE INTO dbo.issues_attachments AS tgt
USING (SELECT * FROM src_deduped WHERE rn = 1) AS src
ON tgt.attachment_id = src.attachment_id
WHEN MATCHED THEN
    UPDATE SET
        issue_id = src.issue_id,
        attachment_name = src.attachment_name,
        attachment_type = src.attachment_type,
        created_by = src.created_by,
        created_at = src.created_at,
        updated_by = src.updated_by,
        updated_at = src.updated_at
WHEN NOT MATCHED THEN
    INSERT (attachment_id, issue_id, attachment_name, attachment_type, created_by, created_at, updated_by, updated_at)
    VALUES (src.attachment_id, src.issue_id, src.attachment_name, src.attachment_type, src.created_by, src.created_at, src.updated_by, src.updated_at);
