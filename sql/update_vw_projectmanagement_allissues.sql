USE ProjectManagement;
GO

CREATE OR ALTER VIEW [dbo].[vw_ProjectManagement_AllIssues] AS

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
-- ACC issues - combine Priority and Clash_Level
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
    CASE WHEN acc.deleted_at IS NOT NULL OR LOWER(ve.status) = 'deleted' THEN 1 ELSE 0 END AS is_deleted
FROM acc_data_schema.dbo.vw_issues_expanded ve
LEFT JOIN acc_data_schema.dbo.issues_issues acc
    ON acc.issue_id = ve.issue_id
LEFT JOIN acc_status_map acc_map
    ON acc_map.raw_status = LOWER(ve.status)

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
    rv.tags_json AS custom_attributes_json,
    TRY_CAST(rv.updated AS DATETIME) AS source_updated_at,
    NULL AS source_load_ts,
    0 AS is_deleted
FROM ReviztoData.dbo.vw_ReviztoProjectIssues_Deconstructed rv
LEFT JOIN ProjectManagement.dbo.revizto_project_map rpm
    ON rpm.revizto_project_uuid = CAST(rv.projectUuid AS NVARCHAR(100))
   AND rpm.is_active = 1
LEFT JOIN ProjectManagement.dbo.projects pm_proj
    ON pm_proj.project_id = rpm.pm_project_id
LEFT JOIN rev_status_map rev_map
    ON rev_map.raw_status = LOWER(rv.status);

GO
