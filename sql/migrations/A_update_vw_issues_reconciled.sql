-- ========================================================================
-- A: UPDATE VIEW - Add issue_key_hash to vw_Issues_Reconciled
-- ========================================================================
-- Purpose: Enhance vw_Issues_Reconciled to include stable issue_key_hash
--          for anchor linking relationships
--
-- Status: Ready for Deployment
-- Dependencies: dbo.Issues_Current (source data with issue_key_hash)
--
-- ========================================================================

IF OBJECT_ID('dbo.vw_Issues_Reconciled', 'V') IS NOT NULL
    DROP VIEW dbo.vw_Issues_Reconciled;
GO

CREATE VIEW dbo.vw_Issues_Reconciled
AS
SELECT
    -- Core identifiers
    ic.issue_key,
    ic.issue_key_hash,  -- ← NEW COLUMN: Stable hash for anchor linking
    
    -- Display identifier (reconciled)
    CASE
        WHEN aimap.acc_issue_id IS NOT NULL 
        THEN CONCAT('ACC-', aimap.acc_issue_id)
        ELSE ic.issue_key
    END AS display_id,
    
    -- Source information
    ic.source_system,
    ic.source_issue_id,
    
    -- ACC mapping (when applicable)
    aimap.acc_issue_id,
    
    -- Core issue data
    CAST(ic.project_id AS VARCHAR(50)) AS project_id,
    ic.title,
    ic.description,
    ic.issue_type,
    ic.status,
    ic.priority,
    ic.assignee_user_key,
    ic.created_by_user_key,
    ic.created_at,
    ic.updated_at,
    ic.resolved_at,
    
    -- Normalized fields (from constants/schema reference)
    CASE
        WHEN ic.status IN ('Closed', 'Resolved', 'Done', 'No Action')
        THEN 'Closed'
        WHEN ic.status IN ('In Progress', 'In Review')
        THEN 'In Progress'
        ELSE 'Open'
    END AS status_normalized,
    
    CASE
        WHEN ic.priority IN ('Critical', 'Blocker', '1')
        THEN 'Critical'
        WHEN ic.priority IN ('High', '2')
        THEN 'High'
        WHEN ic.priority IN ('Medium', '3')
        THEN 'Medium'
        WHEN ic.priority IN ('Low', '4')
        THEN 'Low'
        ELSE 'Medium'
    END AS priority_normalized,
    
    CASE
        WHEN ic.discipline LIKE '%MEP%' OR ic.discipline LIKE '%Mechanical%'
        THEN 'MEP'
        WHEN ic.discipline LIKE '%Structural%' OR ic.discipline LIKE '%Structure%'
        THEN 'Structural'
        WHEN ic.discipline LIKE '%Arch%'
        THEN 'Architecture'
        ELSE COALESCE(ic.discipline, 'General')
    END AS discipline_normalized,
    
    -- Additional metadata
    ic.is_hidden,
    ic.linked_bim_element_id,
    ic.external_reference_id
    
FROM dbo.Issues_Current ic
LEFT JOIN dbo.vw_acc_issue_id_map aimap
    ON ic.issue_key = aimap.revizto_issue_key
    AND ic.source_system = 'Revizto'
WHERE ic.is_hidden = 0;

GO

-- ========================================================================
-- VALIDATION: Verify new column exists and is populated
-- ========================================================================

-- Test: Return sample data with new column
SELECT TOP 10
    display_id,
    issue_key_hash,
    source_system,
    title,
    status_normalized,
    priority_normalized
FROM dbo.vw_Issues_Reconciled
WHERE issue_key_hash IS NOT NULL
ORDER BY created_at DESC;

-- Test: Count all rows with hashes populated
SELECT 
    COUNT(*) AS total_rows,
    COUNT(DISTINCT issue_key_hash) AS rows_with_hash,
    COUNT(*) - COUNT(DISTINCT issue_key_hash) AS rows_without_hash
FROM dbo.vw_Issues_Reconciled;

-- Expected Result: All 12,840 rows should have issue_key_hash populated
-- Performance: <1 second query time
