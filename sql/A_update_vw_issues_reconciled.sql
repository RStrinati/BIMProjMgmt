-- ========================================
-- TASK A: Update vw_Issues_Reconciled to include issue_key_hash
-- ========================================
-- Purpose: Add stable issue_key_hash for anchor linking
-- Change: Additive (new column in SELECT)
-- Risk: Low (LEFT JOIN unchanged, new column from base table)

USE ProjectManagement;
GO

DROP VIEW IF EXISTS dbo.vw_Issues_Reconciled;
GO

CREATE VIEW dbo.vw_Issues_Reconciled AS

SELECT
    ic.issue_key,
    ic.issue_key_hash,  -- NEW: Stable hash for anchor linking
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
    
    -- Smart title: prefer acc_title for mapped ACC issues
    CASE
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
;
GO

PRINT 'View dbo.vw_Issues_Reconciled updated with issue_key_hash column'
GO

-- Validation: Verify issue_key_hash is present
SELECT TOP 10
    issue_key,
    issue_key_hash,
    display_id,
    source_system
FROM dbo.vw_Issues_Reconciled
WHERE issue_key_hash IS NOT NULL
ORDER BY updated_at DESC;
GO
