-- ========================================
-- TASK D: Validation Queries
-- ========================================
-- Purpose: Verify all components are created correctly and working

USE ProjectManagement;
GO

PRINT '====== VALIDATION SUITE ======'
GO

-- ========================================
-- Part 1: Verify vw_Issues_Reconciled has issue_key_hash
-- ========================================
PRINT ''
PRINT '1. Checking vw_Issues_Reconciled structure...'
GO

SELECT 
    'issue_key_hash' AS column_name,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT issue_key_hash) AS distinct_hashes,
    COUNT(CASE WHEN issue_key_hash IS NOT NULL THEN 1 END) AS non_null_count
FROM dbo.vw_Issues_Reconciled;
GO

-- Verify sample rows with hash
PRINT 'Sample rows with issue_key_hash:'
SELECT TOP 5
    issue_key,
    display_id,
    CONVERT(VARCHAR(MAX), CONVERT(VARBINARY(MAX), issue_key_hash), 2) AS hash_hex,
    source_system
FROM dbo.vw_Issues_Reconciled
WHERE issue_key_hash IS NOT NULL
ORDER BY updated_at DESC;
GO

-- ========================================
-- Part 2: Verify IssueAnchorLinks table
-- ========================================
PRINT ''
PRINT '2. Checking IssueAnchorLinks table...'
GO

-- Check table exists
IF OBJECT_ID('dbo.IssueAnchorLinks', 'U') IS NOT NULL
    PRINT '✓ Table dbo.IssueAnchorLinks exists'
ELSE
    PRINT '✗ ERROR: Table dbo.IssueAnchorLinks NOT FOUND'
GO

-- Check constraints
PRINT ''
PRINT 'Constraints in IssueAnchorLinks:'
SELECT
    CONSTRAINT_NAME,
    CONSTRAINT_TYPE
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
WHERE TABLE_NAME = 'IssueAnchorLinks'
    AND TABLE_SCHEMA = 'dbo'
ORDER BY CONSTRAINT_TYPE, CONSTRAINT_NAME;
GO

-- Check indexes
PRINT ''
PRINT 'Indexes on IssueAnchorLinks:'
SELECT DISTINCT
    ix.name AS index_name,
    STUFF((
        SELECT ',' + col_name(ic.object_id, ic.column_id)
        FROM sys.index_columns ic
        WHERE ic.object_id = ix.object_id
            AND ic.index_id = ix.index_id
        FOR XML PATH('')
    ), 1, 1, '') AS columns
FROM sys.indexes ix
WHERE ix.object_id = OBJECT_ID('dbo.IssueAnchorLinks')
    AND ix.index_id > 0
ORDER BY ix.name;
GO

-- ========================================
-- Part 3: Test anchor link creation (insert test data)
-- ========================================
PRINT ''
PRINT '3. Testing IssueAnchorLinks insert and constraints...'
GO

DECLARE @test_issue_hash VARBINARY(32)
DECLARE @test_project INT

-- Get a sample issue hash and project from vw_Issues_Reconciled
SELECT TOP 1
    @test_issue_hash = issue_key_hash,
    @test_project = CAST(project_id AS INT)
FROM dbo.vw_Issues_Reconciled
WHERE issue_key_hash IS NOT NULL
ORDER BY updated_at DESC;

IF @test_issue_hash IS NOT NULL
BEGIN
    PRINT 'Inserting test link with service anchor...'
    INSERT INTO dbo.IssueAnchorLinks (
        project_id,
        issue_key_hash,
        anchor_type,
        service_id,
        link_role,
        note
    ) VALUES (
        @test_project,
        @test_issue_hash,
        'service',
        1,  -- Test service_id
        'blocks',
        'Test anchor link for validation'
    );
    
    PRINT '✓ Test insert successful'
    
    -- Verify test data
    SELECT
        link_id,
        anchor_type,
        service_id,
        link_role,
        note,
        created_at
    FROM dbo.IssueAnchorLinks
    WHERE note = 'Test anchor link for validation'
    ORDER BY link_id DESC;
    
    -- Clean up test data
    DELETE FROM dbo.IssueAnchorLinks
    WHERE note = 'Test anchor link for validation';
    
    PRINT '✓ Test data cleaned up'
END
ELSE
BEGIN
    PRINT '⚠ No sample issue found (view may be empty)'
END
GO

-- ========================================
-- Part 4: Verify helper views
-- ========================================
PRINT ''
PRINT '4. Checking helper views...'
GO

-- Check vw_IssueAnchorLinks_Expanded
IF OBJECT_ID('dbo.vw_IssueAnchorLinks_Expanded', 'V') IS NOT NULL
    PRINT '✓ View dbo.vw_IssueAnchorLinks_Expanded exists'
ELSE
    PRINT '✗ ERROR: View dbo.vw_IssueAnchorLinks_Expanded NOT FOUND'
GO

-- Check vw_AnchorBlockerCounts
IF OBJECT_ID('dbo.vw_AnchorBlockerCounts', 'V') IS NOT NULL
    PRINT '✓ View dbo.vw_AnchorBlockerCounts exists'
ELSE
    PRINT '✗ ERROR: View dbo.vw_AnchorBlockerCounts NOT FOUND'
GO

-- ========================================
-- Part 5: Query performance check
-- ========================================
PRINT ''
PRINT '5. Query performance validation...'
GO

-- Check vw_Issues_Reconciled with issue_key_hash filter
SET STATISTICS TIME ON
SELECT COUNT(*) AS reconciled_issue_count
FROM dbo.vw_Issues_Reconciled
WHERE issue_key_hash IS NOT NULL;
SET STATISTICS TIME OFF
GO

-- ========================================
-- Part 6: Summary
-- ========================================
PRINT ''
PRINT '====== VALIDATION SUMMARY ======'
PRINT ''

-- Count issues with hash available
SELECT
    'vw_Issues_Reconciled' AS component,
    COUNT(*) AS total_records,
    COUNT(CASE WHEN issue_key_hash IS NOT NULL THEN 1 END) AS with_hash
FROM dbo.vw_Issues_Reconciled;

PRINT ''
PRINT 'Validation complete. Check results above.'
GO
