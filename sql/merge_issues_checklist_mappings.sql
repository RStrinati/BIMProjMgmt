-- MERGE for issues_checklist_mappings
WITH src_deduped AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY issue_id, bim360_account_id, bim360_project_id, checklist_id
        ORDER BY checklist_id
    ) AS rn
    FROM staging.issues_checklist_mappings
)
MERGE INTO dbo.issues_checklist_mappings AS tgt
USING (SELECT * FROM src_deduped WHERE rn = 1) AS src
ON tgt.issue_id = src.issue_id
   AND tgt.bim360_account_id = src.bim360_account_id
   AND tgt.bim360_project_id = src.bim360_project_id
   AND tgt.checklist_id = src.checklist_id
WHEN MATCHED THEN
    UPDATE SET
        tgt.checklist_item = src.checklist_item,
        tgt.checklist_section = src.checklist_section
WHEN NOT MATCHED BY TARGET THEN
    INSERT (
        issue_id, bim360_account_id, bim360_project_id, checklist_id,
        checklist_item, checklist_section
    )
    VALUES (
        src.issue_id, src.bim360_account_id, src.bim360_project_id, src.checklist_id,
        src.checklist_item, src.checklist_section
    );
