/*
    Seed staging from ACC expanded issues view
    - Requires: ProjectManagement.dbo.vw_dim_projects and dbo.project_aliases to be present for _pm mapping
*/

USE ProjectManagement;
GO

-- Deduplicate ACC issues per issue_id and bring Priority from the non-_pm view
WITH PM AS (
    SELECT
        pm.issue_id,
        pm.project_name,
        pm.project_id,
        pm.status,
        pm.title,
        pm.description,
        pm.assignee_display_name,
        pm.created_at,
        pm.closed_at,
        pm.latest_comment_at,
        pm.due_date,
        pm.Discipline,
        ROW_NUMBER() OVER (
            PARTITION BY pm.issue_id
            ORDER BY pm.closed_at DESC, pm.created_at DESC, pm.issue_id
        ) AS rn
    FROM acc_data_schema.dbo.vw_issues_expanded_pm pm
), VE AS (
    SELECT
        ve.issue_id,
        ve.Priority,
        ROW_NUMBER() OVER (
            PARTITION BY ve.issue_id
            ORDER BY ve.closed_at DESC, ve.created_at DESC, ve.issue_id
        ) AS rn
    FROM acc_data_schema.dbo.vw_issues_expanded ve
)
INSERT INTO stg.issues (
    source_system,
    issue_id,
    project_name,
    project_id_raw,
    status,
    priority,
    title,
    description,
    assignee,
    author,
    created_at,
    closed_at,
    last_activity_date,
    due_date,
    discipline,
    category_primary,
    category_secondary,
    record_source
)
SELECT
    'ACC' AS source_system,
    PM.issue_id,
    PM.project_name,
    CAST(PM.project_id AS NVARCHAR(255)) AS project_id_raw,
    PM.status,
    COALESCE(VE.Priority, NULL) AS priority,
    PM.title,
    PM.description,
    PM.assignee_display_name,
    NULL AS author,
    PM.created_at,
    PM.closed_at,
    PM.latest_comment_at,
    PM.due_date,
    PM.Discipline,
    NULL AS category_primary,
    NULL AS category_secondary,
    'seed_from_acc.sql'
FROM PM
LEFT JOIN VE ON VE.issue_id = PM.issue_id AND VE.rn = 1
WHERE PM.rn = 1;               -- dedup per issue_id

PRINT 'Seeded stg.issues from ACC';
GO
