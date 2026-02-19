-- vw_Issues_Reconciled: Unified Issues View (ACC + Revizto)
-- Purpose: Single source of truth for all issues with reconciled identifiers
-- Features:
--   - ACC issues: human-friendly display_id (ACC-<number>) when mapped
--   - Revizto issues: REV-<id> format
--   - Smart title fallback: use acc_title for mapped ACC, issue_key otherwise
-- Performance: LEFT JOIN only, no heavy aggregations

USE ProjectManagement;
GO

SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO

DROP VIEW IF EXISTS dbo.vw_Issues_Reconciled;
GO

CREATE VIEW dbo.vw_Issues_Reconciled AS

SELECT
    ic.issue_key,
    ic.source_system,
    ic.source_issue_id,
    ic.source_project_id,
    ic.project_id,
    
    -- Display identifiers (human-friendly)
    CASE 
        WHEN ic.source_system = 'ACC' AND m.acc_issue_number IS NOT NULL 
            THEN 'ACC-' + CAST(m.acc_issue_number AS VARCHAR(20))
        WHEN ic.source_system = 'ACC' 
            THEN 'ACC-' + LEFT(ic.source_issue_id, 8)
        WHEN ic.source_system = 'Revizto'
            THEN 'REV-' + ic.source_issue_id
        ELSE ic.issue_key
    END AS display_id,
    
    -- Enriched ACC identifiers (nullable for Revizto)
    m.acc_issue_number,
    m.acc_issue_uuid,
    m.source_id_type AS acc_id_type,
    
    -- Smart title:
    -- 1) ACC title from acc_data_schema (handles both UUID + display_id paths)
    -- 2) Revizto title from deconstructed view
    -- 3) Fallback to issue_key
    CASE
        WHEN ic.source_system = 'ACC' AND acc.title IS NOT NULL THEN acc.title
        WHEN ic.source_system = 'Revizto' AND rv.title IS NOT NULL THEN rv.title
        WHEN ic.source_system = 'ACC' AND m.acc_title IS NOT NULL THEN m.acc_title
        ELSE ic.issue_key
    END AS title,
    
    ic.status_raw,
    ic.status_normalized,
    ic.priority_raw,
    ic.priority_normalized,
    ic.discipline_raw,
    ic.discipline_normalized,
    ic.assignee_user_key,
    ic.created_at,
    ic.updated_at,
    ic.closed_at,
    ic.created_by,
    ic.updated_by,
    ic.closed_by,
    ic.linked_document_urn,
    ic.snapshot_urn,
    ic.web_link,
    ic.preview_middle_url,
    ic.issue_link,
    ic.snapshot_preview_url,
    ic.location_root,
    ic.location_building,
    ic.location_level,
    
    -- ACC enrichment
    m.acc_status,
    m.acc_created_at,
    m.acc_updated_at,
    m.acc_title,
    
    ic.import_run_id,
    ic.is_deleted,
    ic.project_mapped

FROM dbo.Issues_Current ic
LEFT JOIN dbo.vw_acc_issue_id_map m
    ON ic.source_system = 'ACC'
    AND ic.source_issue_id = m.source_issue_id
    AND ic.source_project_id = m.source_project_id
LEFT JOIN acc_data_schema.dbo.issues_issues acc
    ON ic.source_system = 'ACC'
    AND (
        ic.source_issue_id = CAST(acc.issue_id AS NVARCHAR(MAX))
        OR (
            TRY_CAST(ic.source_issue_id AS INT) = acc.display_id
            AND ic.acc_project_id = acc.bim360_project_id
        )
    )
LEFT JOIN ProjectManagement.dbo.revizto_project_map rpm
    ON ic.source_system = 'Revizto'
    AND rpm.pm_project_id = ic.project_id
    AND rpm.is_active = 1
LEFT JOIN ReviztoData.dbo.tblReviztoProjects rvp
    ON ic.source_system = 'Revizto'
    AND rpm.revizto_project_uuid = rvp.projectUuid
LEFT JOIN ReviztoData.dbo.vw_ReviztoProjectIssues_Deconstructed rv
    ON ic.source_system = 'Revizto'
    AND rpm.revizto_project_uuid = rv.projectUuid
    AND (
        ic.source_issue_id = CAST(rv.issueId AS NVARCHAR(100))
        OR ic.source_issue_id = CAST(rv.issue_number AS NVARCHAR(100))
    )
;
GO

PRINT 'View dbo.vw_Issues_Reconciled created'
GO

-- Test: summary by source
SELECT 
    source_system,
    COUNT(*) as total_rows,
    COUNT(CASE WHEN display_id LIKE 'ACC-%' THEN 1 END) as acc_count,
    COUNT(CASE WHEN display_id LIKE 'REV-%' THEN 1 END) as revizto_count,
    COUNT(CASE WHEN acc_issue_number IS NOT NULL THEN 1 END) as acc_mapped
FROM dbo.vw_Issues_Reconciled
GROUP BY source_system
ORDER BY source_system;
GO
