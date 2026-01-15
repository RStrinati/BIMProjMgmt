-- Validation Queries for ACC Issue Identifier Reconciliation
-- Use these to verify that the mapping view and warehouse updates are correct

USE ProjectManagement;
GO

PRINT '===== VALIDATION TEST SUITE: ACC Issue Identifier Reconciliation =====';
GO

-- TEST 1: Verify vw_acc_issue_id_map exists and has data
PRINT 'TEST 1: vw_acc_issue_id_map data availability';
SELECT
    COUNT(*) as total_rows,
    COUNT(DISTINCT issue_key) as unique_issues,
    COUNT(DISTINCT source_id_type) as id_type_count,
    STRING_AGG(DISTINCT source_id_type, ', ') as id_types
FROM dbo.vw_acc_issue_id_map;
GO

-- TEST 2: Verify UUID path (77.84% of ACC issues)
PRINT 'TEST 2: UUID-based matches (typical case)';
SELECT
    COUNT(*) as uuid_matches,
    COUNT(DISTINCT issue_key) as unique_issues,
    COUNT(DISTINCT acc_issue_number) as unique_display_ids,
    MIN(acc_issue_number) as min_display_id,
    MAX(acc_issue_number) as max_display_id
FROM dbo.vw_acc_issue_id_map
WHERE source_id_type = 'uuid';
GO

-- TEST 3: Verify numeric/display_id path (22.16% of ACC issues)
PRINT 'TEST 3: Numeric/display_id-based matches (fallback case)';
SELECT
    COUNT(*) as numeric_matches,
    COUNT(DISTINCT issue_key) as unique_issues
FROM dbo.vw_acc_issue_id_map
WHERE source_id_type = 'display_id';
GO

-- TEST 4: Sample UUID matches - show examples
PRINT 'TEST 4: Sample UUID matches with both identifiers';
SELECT TOP 10
    issue_key,
    source_issue_id,
    acc_issue_uuid,
    acc_issue_number,
    acc_title,
    acc_status,
    acc_created_at
FROM dbo.vw_acc_issue_id_map
WHERE source_id_type = 'uuid'
ORDER BY acc_issue_number;
GO

-- TEST 5: Check for duplicates in mapping (should be 1:1)
PRINT 'TEST 5: Check for duplicate mappings (should be 0)';
SELECT
    issue_key,
    COUNT(*) as mapping_count
FROM dbo.vw_acc_issue_id_map
GROUP BY issue_key
HAVING COUNT(*) > 1;
GO

-- TEST 6: Verify issue count consistency
PRINT 'TEST 6: Issue count consistency check';
DECLARE @total_acc_in_current INT = (SELECT COUNT(*) FROM dbo.Issues_Current WHERE source_system='ACC');
DECLARE @total_acc_in_map INT = (SELECT COUNT(DISTINCT issue_key) FROM dbo.vw_acc_issue_id_map);

SELECT
    @total_acc_in_current as total_in_Issues_Current,
    @total_acc_in_map as total_in_mapping_view,
    @total_acc_in_current - @total_acc_in_map as unmapped_count,
    CASE 
        WHEN @total_acc_in_current = @total_acc_in_map THEN 'PASS: All issues mapped'
        ELSE 'WARNING: ' + CAST((@total_acc_in_current - @total_acc_in_map) AS NVARCHAR(20)) + ' issues unmapped'
    END as validation_result;
GO

-- TEST 7: Verify no duplicate acc_issue_numbers per ACC project
PRINT 'TEST 7: Verify acc_issue_number uniqueness (should be no duplicates)';
SELECT
    acc_project_uuid,
    acc_issue_number,
    COUNT(*) as occurrence_count
FROM dbo.vw_acc_issue_id_map
WHERE source_id_type = 'uuid'
GROUP BY acc_project_uuid, acc_issue_number
HAVING COUNT(*) > 1;
GO

-- TEST 8: Show distribution of id_type
PRINT 'TEST 8: Distribution of source_id_type';
SELECT
    source_id_type,
    COUNT(DISTINCT issue_key) as issue_count,
    CAST(100.0 * COUNT(DISTINCT issue_key) / (SELECT COUNT(DISTINCT issue_key) FROM dbo.vw_acc_issue_id_map) AS DECIMAL(5,2)) as pct
FROM dbo.vw_acc_issue_id_map
GROUP BY source_id_type
ORDER BY issue_count DESC;
GO

-- TEST 9: Verify vw_ProjectManagement_AllIssues includes new columns
PRINT 'TEST 9: Verify updated vw_ProjectManagement_AllIssues';
SELECT
    COUNT(*) as total_issues,
    SUM(CASE WHEN source = 'ACC' THEN 1 ELSE 0 END) as acc_issues,
    SUM(CASE WHEN source = 'ACC' AND acc_issue_number IS NOT NULL THEN 1 ELSE 0 END) as acc_with_number,
    SUM(CASE WHEN source = 'ACC' AND acc_issue_uuid IS NOT NULL THEN 1 ELSE 0 END) as acc_with_uuid
FROM dbo.vw_ProjectManagement_AllIssues;
GO

-- TEST 10: Sample data from vw_ProjectManagement_AllIssues
PRINT 'TEST 10: Sample ACC issues from vw_ProjectManagement_AllIssues (new columns)';
SELECT TOP 5
    issue_id,
    source_issue_id,
    acc_issue_number,
    acc_issue_uuid,
    acc_id_type,
    title,
    status,
    source
FROM dbo.vw_ProjectManagement_AllIssues
WHERE source = 'ACC'
ORDER BY issue_id;
GO

-- TEST 11: Verify dashboard impact - issue counts should be unchanged
PRINT 'TEST 11: Dashboard impact verification - issue counts';
DECLARE @acc_total_old INT = (SELECT COUNT(*) FROM dbo.Issues_Current WHERE source_system='ACC');
DECLARE @acc_total_view INT = (SELECT COUNT(CASE WHEN source='ACC' THEN 1 END) FROM dbo.vw_ProjectManagement_AllIssues);
DECLARE @rev_total_view INT = (SELECT COUNT(CASE WHEN source='Revizto' THEN 1 END) FROM dbo.vw_ProjectManagement_AllIssues);

SELECT
    'ACC (from Issues_Current)' as source_count_from,
    @acc_total_old as count_value
UNION ALL
SELECT 'ACC (from vw_ProjectManagement_AllIssues)', @acc_total_view
UNION ALL
SELECT 'Revizto (from vw_ProjectManagement_AllIssues)', @rev_total_view
UNION ALL
SELECT 
    'Status', 
    CASE 
        WHEN @acc_total_old = @acc_total_view THEN 'PASS: Counts match'
        ELSE 'FAIL: Count mismatch'
    END
GO

-- TEST 12: Identify any unmapped ACC issues
PRINT 'TEST 12: Unmapped ACC issues (should be empty)';
SELECT
    ic.issue_key,
    ic.source_issue_id,
    ic.source_project_id,
    ic.title
FROM dbo.Issues_Current ic
WHERE ic.source_system = 'ACC'
    AND ic.issue_key NOT IN (SELECT issue_key FROM dbo.vw_acc_issue_id_map)
ORDER BY ic.created_at DESC;
GO

PRINT '===== END VALIDATION SUITE =====';
GO
