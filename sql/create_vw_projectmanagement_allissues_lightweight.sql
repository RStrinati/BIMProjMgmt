-- Create vw_ProjectManagement_AllIssues_Lightweight
-- This is a cleaner alternative that uses vw_acc_issue_id_map for ACC issues
-- Avoids the performance issues with recreating the heavy original view

USE ProjectManagement;
GO

CREATE VIEW dbo.vw_ProjectManagement_AllIssues_Lightweight AS

-- ACC issues (via optimized mapping view)
SELECT
    mapping.issue_key,
    'ACC' AS source,
    CAST(mapping.acc_issue_number AS NVARCHAR(100)) AS issue_id,
    mapping.source_issue_id,
    mapping.acc_title AS title,
    mapping.acc_status AS status,
    mapping.acc_status AS status_normalized,
    mapping.acc_created_at AS created_at,
    mapping.acc_updated_at AS closed_at,
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
    -- New columns (populated for ACC)
    mapping.acc_issue_uuid,
    mapping.acc_issue_number,
    mapping.source_id_type AS acc_id_type
FROM dbo.vw_acc_issue_id_map mapping

UNION ALL

-- Revizto issues (simplified)
SELECT
    CONCAT('Revizto|', source_project_id, '|', source_issue_id) AS issue_key,
    'Revizto' AS source,
    source_issue_id AS issue_id,
    source_issue_id,
    title,
    status,
    status AS status_normalized,
    created_at,
    closed_at,
    assignee,
    author,
    project_name,
    project_id,
    source_project_id,
    pm_project_id,
    project_mapped,
    priority,
    web_link,
    preview_middle_url,
    NULL AS phase,
    NULL AS building_level,
    NULL AS clash_level,
    NULL AS custom_attributes_json,
    source_updated_at,
    source_load_ts,
    is_deleted,
    -- New columns (NULL for Revizto)
    NULL AS acc_issue_uuid,
    NULL AS acc_issue_number,
    NULL AS acc_id_type
FROM dbo.v_revizto_issues_detail
;
GO

PRINT 'vw_ProjectManagement_AllIssues_Lightweight created successfully'
GO

-- Verify it works
SELECT TOP 5 source, COUNT(*) as row_count 
FROM dbo.vw_ProjectManagement_AllIssues_Lightweight 
GROUP BY source
GO
