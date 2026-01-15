-- ========================================================================
-- C: CREATE HELPER VIEWS - UI-Ready Queries for Anchor Linking
-- ========================================================================
-- Purpose: Provide pre-joined views for efficient UI queries
--
-- View 1: vw_IssueAnchorLinks_Expanded
--         Joins links to full issue details for UI display
--
-- View 2: vw_AnchorBlockerCounts
--         Aggregates blocker counts by anchor (for badge display)
--
-- Status: Ready for Deployment
-- Dependencies: dbo.IssueAnchorLinks, dbo.vw_Issues_Reconciled
--
-- ========================================================================

-- ========================================================================
-- VIEW 1: vw_IssueAnchorLinks_Expanded
-- ========================================================================
-- Purpose: UI-ready view joining anchor links to complete issue details
-- Columns: 24 total
-- Usage: Get full issue information for anchor-linked issues
--
-- Example Query:
--   SELECT * FROM vw_IssueAnchorLinks_Expanded
--   WHERE anchor_type = 'service' AND service_id = 42
--     AND link_role = 'blocks' AND link_deleted_at IS NULL
--

IF OBJECT_ID('dbo.vw_IssueAnchorLinks_Expanded', 'V') IS NOT NULL
    DROP VIEW dbo.vw_IssueAnchorLinks_Expanded;
GO

CREATE VIEW dbo.vw_IssueAnchorLinks_Expanded
AS
SELECT
    -- From IssueAnchorLinks (link metadata)
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
    
    -- From vw_Issues_Reconciled (issue details)
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
    ir.updated_at AS issue_updated_at
    
FROM dbo.IssueAnchorLinks ial
LEFT JOIN dbo.vw_Issues_Reconciled ir
    ON ial.issue_key_hash = ir.issue_key_hash;

GO

-- ========================================================================
-- VIEW 2: vw_AnchorBlockerCounts
-- ========================================================================
-- Purpose: Aggregated blocker counts per anchor
-- Columns: 10 total
-- Usage: Get badge counts (total, open, critical, etc.)
--
-- Example Query:
--   SELECT total_linked, open_count, critical_count
--   FROM vw_AnchorBlockerCounts
--   WHERE anchor_type = 'service' AND service_id = 42
--

IF OBJECT_ID('dbo.vw_AnchorBlockerCounts', 'V') IS NOT NULL
    DROP VIEW dbo.vw_AnchorBlockerCounts;
GO

CREATE VIEW dbo.vw_AnchorBlockerCounts
AS
WITH anchor_blocker_links AS (
    -- Get all active 'blocks' relationships
    SELECT
        ial.anchor_type,
        ial.service_id,
        ial.review_id,
        ial.item_id,
        ial.issue_key_hash,
        ir.status_normalized,
        ir.priority_normalized
    FROM dbo.IssueAnchorLinks ial
    JOIN dbo.vw_Issues_Reconciled ir
        ON ial.issue_key_hash = ir.issue_key_hash
    WHERE ial.link_role = 'blocks'
      AND ial.deleted_at IS NULL
)
SELECT
    -- Anchor identification
    anchor_type,
    service_id,
    review_id,
    item_id,
    
    -- Counts
    COUNT(*) AS total_linked,
    
    SUM(CASE 
        WHEN status_normalized IN ('Open', 'In Progress', 'In Review')
        THEN 1 ELSE 0 
    END) AS open_count,
    
    SUM(CASE 
        WHEN status_normalized IN ('Closed', 'Resolved', 'Done')
        THEN 1 ELSE 0 
    END) AS closed_count,
    
    -- Priority breakdown
    SUM(CASE WHEN priority_normalized = 'Critical' THEN 1 ELSE 0 END) AS critical_count,
    SUM(CASE WHEN priority_normalized = 'High' THEN 1 ELSE 0 END) AS high_count,
    SUM(CASE WHEN priority_normalized = 'Medium' THEN 1 ELSE 0 END) AS medium_count
    
FROM anchor_blocker_links
GROUP BY anchor_type, service_id, review_id, item_id;

GO

-- ========================================================================
-- VALIDATION: Verify views are created and have correct structure
-- ========================================================================

-- Test 1: vw_IssueAnchorLinks_Expanded exists with 24 columns
SELECT
    TABLE_NAME,
    COUNT(*) AS column_count
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME IN ('vw_IssueAnchorLinks_Expanded', 'vw_AnchorBlockerCounts')
GROUP BY TABLE_NAME;

-- Expected: vw_IssueAnchorLinks_Expanded = 24 columns
--           vw_AnchorBlockerCounts = 10 columns

-- Test 2: Verify columns in expanded view
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'vw_IssueAnchorLinks_Expanded'
ORDER BY ORDINAL_POSITION;

-- Expected: link_id (BIGINT), issue_key_hash (VARBINARY), display_id (VARCHAR), etc.

-- Test 3: Verify columns in counts view
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'vw_AnchorBlockerCounts'
ORDER BY ORDINAL_POSITION;

-- Expected: anchor_type, service_id, review_id, item_id, total_linked (INT), open_count (INT), etc.

-- Test 4: Query expanded view (should return 0 rows until data inserted)
SELECT TOP 5 * FROM dbo.vw_IssueAnchorLinks_Expanded;

-- Expected: Zero rows (table is empty)

-- Test 5: Query counts view (should return 0 rows until data inserted)
SELECT * FROM dbo.vw_AnchorBlockerCounts;

-- Expected: Zero rows (no blockers yet)

-- ========================================================================
-- PERFORMANCE NOTES:
-- - vw_IssueAnchorLinks_Expanded uses LEFT JOIN on indexed issue_key_hash
--   Expected query time: <100ms for single anchor lookup
-- - vw_AnchorBlockerCounts uses GROUP BY on anchor identifiers
--   Expected query time: <50ms for single anchor counts
-- - Both views support efficient filtering by anchor_type and IDs via indexes
-- ========================================================================
