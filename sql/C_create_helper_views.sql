-- ========================================
-- TASK C: Helper Views for UI Consumption
-- ========================================
-- Purpose: Provide expanded issue data with link information
--   and aggregated blocker counts for UI badges

USE ProjectManagement;
GO

-- ========================================
-- View 1: vw_IssueAnchorLinks_Expanded
-- ========================================
-- Purpose: Join anchor links to issue details for UI consumption
-- Output: All issue fields + link information
-- Performance: Single LEFT JOIN, indexed on issue_key_hash

DROP VIEW IF EXISTS dbo.vw_IssueAnchorLinks_Expanded;
GO

CREATE VIEW dbo.vw_IssueAnchorLinks_Expanded AS

SELECT
    -- Link information
    ial.link_id,
    ial.issue_key_hash,
    ial.anchor_type,
    ial.service_id,
    ial.review_id,
    ial.item_id,
    ial.link_role,
    ial.note,
    ial.created_at AS link_created_at,
    ial.created_by AS link_created_by,
    ial.deleted_at AS link_deleted_at,
    
    -- Issue information (from vw_Issues_Reconciled)
    ir.issue_key,
    ir.display_id,
    ir.source_system,
    ir.source_issue_id,
    ir.project_id,
    ir.title,
    ir.status_normalized,
    ir.priority_normalized,
    ir.discipline_normalized,
    ir.assignee_user_key,
    ir.created_at AS issue_created_at,
    ir.updated_at AS issue_updated_at,
    
    -- Derived for UI
    CASE 
        WHEN ir.status_normalized IN ('Open', 'In Progress', 'In Review') THEN 1
        ELSE 0
    END AS is_open

FROM dbo.IssueAnchorLinks ial
LEFT JOIN dbo.vw_Issues_Reconciled ir
    ON ial.issue_key_hash = ir.issue_key_hash
WHERE ial.deleted_at IS NULL;
GO

PRINT 'View dbo.vw_IssueAnchorLinks_Expanded created'
GO

-- ========================================
-- View 2: vw_AnchorBlockerCounts
-- ========================================
-- Purpose: Aggregated blocker issue counts per anchor (for badges)
-- Output: Per anchor, count total linked issues + breakdown by status/priority
-- Used for: Badge counts in UI (show "3 blockers", "1 critical")

DROP VIEW IF EXISTS dbo.vw_AnchorBlockerCounts;
GO

CREATE VIEW dbo.vw_AnchorBlockerCounts AS

WITH anchor_links AS (
    -- Get all non-deleted links that are "blockers"
    SELECT
        ial.anchor_type,
        ial.service_id,
        ial.review_id,
        ial.item_id,
        ir.status_normalized,
        ir.priority_normalized
    FROM dbo.IssueAnchorLinks ial
    LEFT JOIN dbo.vw_Issues_Reconciled ir
        ON ial.issue_key_hash = ir.issue_key_hash
    WHERE ial.deleted_at IS NULL
        AND ial.link_role = 'blocks'
)
SELECT
    anchor_type,
    service_id,
    review_id,
    item_id,
    
    -- Overall counts
    COUNT(*) AS total_linked,
    
    -- Status breakdown
    COUNT(CASE WHEN status_normalized IN ('Open', 'In Progress', 'In Review') THEN 1 END) AS open_count,
    COUNT(CASE WHEN status_normalized = 'Closed' THEN 1 END) AS closed_count,
    
    -- Priority breakdown
    COUNT(CASE WHEN priority_normalized = 'Critical' THEN 1 END) AS critical_count,
    COUNT(CASE WHEN priority_normalized = 'High' THEN 1 END) AS high_count,
    COUNT(CASE WHEN priority_normalized = 'Medium' THEN 1 END) AS medium_count,
    COUNT(CASE WHEN priority_normalized = 'Low' THEN 1 END) AS low_count

FROM anchor_links
GROUP BY
    anchor_type,
    service_id,
    review_id,
    item_id;
GO

PRINT 'View dbo.vw_AnchorBlockerCounts created'
GO

-- ========================================
-- Validation: Verify views are created
-- ========================================

-- Check vw_IssueAnchorLinks_Expanded structure
SELECT 
    COLUMN_NAME,
    DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'vw_IssueAnchorLinks_Expanded'
    AND TABLE_SCHEMA = 'dbo'
ORDER BY ORDINAL_POSITION;
GO

-- Check vw_AnchorBlockerCounts structure
SELECT 
    COLUMN_NAME,
    DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'vw_AnchorBlockerCounts'
    AND TABLE_SCHEMA = 'dbo'
ORDER BY ORDINAL_POSITION;
GO
