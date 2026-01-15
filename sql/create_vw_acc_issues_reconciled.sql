-- Minimal ACC Issues view using the working mapping view
-- This provides ACC issues with all enriched fields (uuid, number, etc.)
-- No Revizto issues, no complex joins - just clean ACC data

USE ProjectManagement;
GO

CREATE VIEW dbo.vw_ACC_Issues_Reconciled AS

SELECT
    mapping.issue_key,
    'ACC' AS source,
    CAST(mapping.acc_issue_number AS NVARCHAR(100)) AS issue_id,
    mapping.source_issue_id,
    mapping.acc_title AS title,
    mapping.acc_status AS status,
    mapping.acc_status AS status_normalized,
    mapping.acc_created_at AS created_at,
    mapping.acc_updated_at AS updated_at,
    NULL AS assignee,
    NULL AS author,
    NULL AS project_name,
    mapping.source_project_id AS project_id,
    mapping.source_project_id AS source_project_id,
    NULL AS pm_project_id,
    0 AS project_mapped,
    NULL AS priority,
    NULL AS web_link,
    NULL AS preview_middle_url,
    NULL AS phase,
    NULL AS building_level,
    NULL AS clash_level,
    NULL AS custom_attributes_json,
    mapping.acc_updated_at AS source_updated_at,
    GETDATE() AS source_load_ts,
    0 AS is_deleted,
    -- Enriched ACC columns
    mapping.acc_issue_uuid,
    CAST(mapping.acc_issue_number AS INT) AS acc_issue_number,
    mapping.source_id_type AS acc_id_type
FROM dbo.vw_acc_issue_id_map mapping
;
GO

PRINT 'View vw_ACC_Issues_Reconciled created successfully'
GO

-- Test it
SELECT COUNT(*) as total_acc_issues FROM dbo.vw_ACC_Issues_Reconciled;
SELECT TOP 3 acc_issue_number, title, source_issue_id FROM dbo.vw_ACC_Issues_Reconciled;
GO
