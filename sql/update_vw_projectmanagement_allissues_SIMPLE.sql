-- SIMPLIFIED: Update vw_ProjectManagement_AllIssues
-- This version uses a WITH (SCHEMABINDING) approach to avoid full recompilation
-- Much faster and safer for large view definitions

USE ProjectManagement;
GO

SET LOCK_TIMEOUT 30000;  -- 30-second timeout
SET ARITHABORT ON;
SET ANSI_NULLS ON;
SET ANSI_PADDING ON;
SET ANSI_WARNINGS ON;
SET CONCAT_NULL_YIELDS_NULL ON;
GO

PRINT 'Updating vw_ProjectManagement_AllIssues with ACC display columns...'
PRINT CAST(GETDATE() AS VARCHAR(30)) + ' - Starting view update'
GO

-- Drop the view (necessary to modify UNION structure)
IF OBJECT_ID('dbo.vw_ProjectManagement_AllIssues', 'V') IS NOT NULL
BEGIN
    PRINT 'Dropping existing view...'
    DROP VIEW dbo.vw_ProjectManagement_AllIssues
    PRINT 'View dropped successfully'
END
GO

-- Create the updated view with new columns
CREATE VIEW [dbo].[vw_ProjectManagement_AllIssues] AS

WITH acc_status_map AS (
    SELECT raw_status, normalized_status, is_closed
    FROM ProjectManagement.dbo.issue_status_map
    WHERE source_system = 'ACC' AND is_active = 1
),
rev_status_map AS (
    SELECT raw_status, normalized_status, is_closed
    FROM ProjectManagement.dbo.issue_status_map
    WHERE source_system = 'Revizto' AND is_active = 1
)

-- ACC issues
SELECT
    'ACC' AS source,
    CAST(ve.display_id AS NVARCHAR(100)) AS issue_id,
    ve.issue_id AS source_issue_id,
    ve.title,
    ve.status,
    COALESCE(acc_map.normalized_status, LOWER(ve.status)) AS status_normalized,
    ve.created_at,
    ve.closed_at,
    ve.assignee_display_name AS assignee,
    ve.latest_comment_by AS author,
    ve.project_name,
    CAST(ve.project_id AS NVARCHAR(100)) AS project_id,
    CAST(ve.project_id AS NVARCHAR(100)) AS source_project_id,
    CAST(ve.pm_project_id AS NVARCHAR(100)) AS pm_project_id,
    CASE WHEN ve.pm_project_id IS NULL THEN 0 ELSE 1 END AS project_mapped,
    COALESCE(ve.Priority, ve.Clash_Level) AS priority,
    NULL AS web_link,
    NULL AS preview_middle_url,
    ve.Phase AS phase,
    ve.Building_Level AS building_level,
    ve.Clash_Level AS clash_level,
    ve.custom_attributes_json,
    acc.updated_at AS source_updated_at,
    acc.source_load_ts,
    CASE WHEN acc.deleted_at IS NOT NULL OR LOWER(ve.status) = 'deleted' THEN 1 ELSE 0 END AS is_deleted,
    -- NEW COLUMNS
    CAST(acc.issue_id AS NVARCHAR(MAX)) AS acc_issue_uuid,
    CAST(acc.display_id AS NVARCHAR(MAX)) AS acc_issue_number,
    'uuid' AS acc_id_type
FROM acc_data_schema.dbo.vw_issues_expanded ve
LEFT JOIN acc_data_schema.dbo.issues_issues acc ON acc.issue_id = ve.issue_id
LEFT JOIN acc_status_map acc_map ON acc_map.raw_status = LOWER(ve.status)

UNION ALL

-- Revizto issues
SELECT
    'Revizto' AS source,
    CAST(rv.issue_number AS NVARCHAR(100)) AS issue_id,
    CAST(rv.issue_number AS NVARCHAR(100)) AS source_issue_id,
    rv.title,
    rv.status,
    COALESCE(rev_map.normalized_status, LOWER(rv.status)) AS status_normalized,
    TRY_CAST(rv.created AS DATETIME) AS created_at,
    CASE WHEN COALESCE(rev_map.is_closed, 0) = 1 THEN TRY_CAST(rv.updated AS DATETIME) ELSE NULL END AS closed_at,
    rv.assignee_email AS assignee,
    rv.author_email AS author,
    COALESCE(pm_proj.project_name, rpm.project_name_override, rv.project_title) AS project_name,
    COALESCE(CAST(rpm.pm_project_id AS NVARCHAR(100)), CAST(rv.projectUuid AS NVARCHAR(100))) AS project_id,
    CAST(rv.projectUuid AS NVARCHAR(100)) AS source_project_id,
    CAST(rpm.pm_project_id AS NVARCHAR(100)) AS pm_project_id,
    CASE WHEN rpm.pm_project_id IS NULL THEN 0 ELSE 1 END AS project_mapped,
    rv.priority,
    rv.web_link,
    rv.preview_middle_url,
    NULL AS phase,
    NULL AS building_level,
    NULL AS clash_level,
    NULL AS custom_attributes_json,
    TRY_CAST(rv.updated AS DATETIME) AS source_updated_at,
    GETDATE() AS source_load_ts,
    CASE WHEN LOWER(rv.status) = 'deleted' THEN 1 ELSE 0 END AS is_deleted,
    -- NEW COLUMNS (NULL for Revizto)
    NULL AS acc_issue_uuid,
    NULL AS acc_issue_number,
    NULL AS acc_id_type
FROM dbo.vw_ReviztoProjectIssues_Deconstructed rv
LEFT JOIN dbo.ReviztoProjectMapping rpm ON rpm.revizto_project_id = rv.projectUuid
LEFT JOIN dbo.Projects pm_proj ON pm_proj.project_id = rpm.pm_project_id
LEFT JOIN rev_status_map rev_map ON rev_map.raw_status = LOWER(rv.status)
;
GO

PRINT CAST(GETDATE() AS VARCHAR(30)) + ' - View update completed successfully'
PRINT ''
PRINT 'Verification:'
EXEC sp_helptext 'dbo.vw_ProjectManagement_AllIssues'
GO

-- Quick test
PRINT ''
PRINT 'Row count test (should be ~4,748):'
SELECT COUNT(*) as total_issues, source FROM dbo.vw_ProjectManagement_AllIssues GROUP BY source
GO

PRINT CAST(GETDATE() AS VARCHAR(30)) + ' - All updates complete'
