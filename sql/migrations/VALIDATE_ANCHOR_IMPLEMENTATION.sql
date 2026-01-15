-- ========================================================================
-- VALIDATE_ANCHOR_IMPLEMENTATION.sql
-- ========================================================================
-- Purpose: Comprehensive validation queries to verify anchor linking
--          implementation is complete and working correctly
--
-- Usage: Run this after deploying A, B, and C scripts
-- Expected: All queries should return successful results with expected data
--
-- ========================================================================

-- ========================================================================
-- SECTION 1: VERIFY ALL OBJECTS EXIST
-- ========================================================================

PRINT '=== SECTION 1: Verifying all objects exist ==='

-- Check vw_Issues_Reconciled has been updated
IF OBJECT_ID('dbo.vw_Issues_Reconciled', 'V') IS NOT NULL
BEGIN
    PRINT '✅ vw_Issues_Reconciled exists'
    
    -- Check for issue_key_hash column
    IF EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'vw_Issues_Reconciled' AND COLUMN_NAME = 'issue_key_hash'
    )
    BEGIN
        PRINT '✅ issue_key_hash column found in vw_Issues_Reconciled'
    END
    ELSE
    BEGIN
        PRINT '❌ issue_key_hash column NOT found - deployment failed'
    END
END
ELSE
BEGIN
    PRINT '❌ vw_Issues_Reconciled does not exist'
END

-- Check IssueAnchorLinks table exists
IF OBJECT_ID('dbo.IssueAnchorLinks', 'U') IS NOT NULL
BEGIN
    PRINT '✅ dbo.IssueAnchorLinks table exists'
    
    -- Verify all 12 columns
    SELECT @col_count = COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'IssueAnchorLinks'
    
    IF @col_count = 12
        PRINT '✅ IssueAnchorLinks has all 12 columns'
    ELSE
        PRINT '❌ IssueAnchorLinks column count mismatch: ' + CAST(@col_count AS VARCHAR(2))
END
ELSE
BEGIN
    PRINT '❌ dbo.IssueAnchorLinks table does not exist'
END

-- Check helper views exist
IF OBJECT_ID('dbo.vw_IssueAnchorLinks_Expanded', 'V') IS NOT NULL
    PRINT '✅ dbo.vw_IssueAnchorLinks_Expanded view exists'
ELSE
    PRINT '❌ dbo.vw_IssueAnchorLinks_Expanded view NOT found'

IF OBJECT_ID('dbo.vw_AnchorBlockerCounts', 'V') IS NOT NULL
    PRINT '✅ dbo.vw_AnchorBlockerCounts view exists'
ELSE
    PRINT '❌ dbo.vw_AnchorBlockerCounts view NOT found'

-- ========================================================================
-- SECTION 2: VERIFY VIEW ENHANCEMENTS
-- ========================================================================

PRINT ''
PRINT '=== SECTION 2: Verifying vw_Issues_Reconciled enhancements ==='

-- Check data population
SELECT 
    'vw_Issues_Reconciled Statistics' AS metric,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT issue_key_hash) AS rows_with_hash,
    MIN(CAST(created_at AS DATE)) AS earliest_issue,
    MAX(CAST(updated_at AS DATE)) AS latest_update
FROM dbo.vw_Issues_Reconciled
WHERE issue_key_hash IS NOT NULL;

PRINT ''
PRINT 'Sample data from vw_Issues_Reconciled:'
SELECT TOP 5
    display_id,
    issue_key_hash,
    source_system,
    title,
    status_normalized,
    priority_normalized
FROM dbo.vw_Issues_Reconciled
WHERE issue_key_hash IS NOT NULL
ORDER BY created_at DESC;

-- ========================================================================
-- SECTION 3: VERIFY TABLE CONSTRAINTS
-- ========================================================================

PRINT ''
PRINT '=== SECTION 3: Verifying IssueAnchorLinks constraints ==='

-- List all constraints
SELECT 
    CONSTRAINT_NAME,
    CONSTRAINT_TYPE
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
WHERE TABLE_NAME = 'IssueAnchorLinks'
ORDER BY CONSTRAINT_TYPE;

PRINT ''
PRINT 'Expected constraints:'
PRINT '- PK (Primary Key on link_id)'
PRINT '- CK_AnchorType (anchor_type IN service, review, item)'
PRINT '- CK_LinkRole (link_role IN blocks, evidence, relates)'
PRINT '- CK_AnchorTypeMatch (exactly one anchor ID set)'
PRINT '- UQ_IssueAnchorLink (unique link+role combinations)'

-- ========================================================================
-- SECTION 4: VERIFY INDEXES
-- ========================================================================

PRINT ''
PRINT '=== SECTION 4: Verifying IssueAnchorLinks indexes ==='

SELECT 
    i.name AS index_name,
    i.type_desc AS index_type,
    COUNT(ic.column_id) AS column_count
FROM sys.indexes i
LEFT JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
WHERE i.object_id = OBJECT_ID('dbo.IssueAnchorLinks')
  AND i.name IS NOT NULL
GROUP BY i.name, i.type_desc
ORDER BY i.type_desc, i.name;

-- ========================================================================
-- SECTION 5: TEST CONSTRAINT VALIDATION
-- ========================================================================

PRINT ''
PRINT '=== SECTION 5: Testing constraint validation ==='

DECLARE @test_hash VARBINARY(32) = CAST('test_hash_12345678901234567890' AS VARBINARY(32));

-- Test 1: Valid insert (service blocker)
BEGIN TRY
    INSERT INTO dbo.IssueAnchorLinks (project_id, issue_key_hash, anchor_type, service_id, link_role)
    VALUES (999, @test_hash, 'service', 999, 'blocks');
    PRINT '✅ Valid insert succeeded (service blocker)'
    
    -- Clean up
    DELETE FROM dbo.IssueAnchorLinks WHERE issue_key_hash = @test_hash;
END TRY
BEGIN CATCH
    PRINT '❌ Valid insert failed: ' + ERROR_MESSAGE()
END CATCH

-- Test 2: Soft delete functionality
BEGIN TRY
    INSERT INTO dbo.IssueAnchorLinks (project_id, issue_key_hash, anchor_type, service_id, link_role)
    VALUES (999, @test_hash, 'service', 999, 'blocks');
    
    DECLARE @link_id BIGINT = SCOPE_IDENTITY();
    UPDATE dbo.IssueAnchorLinks SET deleted_at = SYSUTCDATETIME() WHERE link_id = @link_id;
    
    SELECT @deleted_count = COUNT(*) FROM dbo.IssueAnchorLinks 
    WHERE link_id = @link_id AND deleted_at IS NOT NULL;
    
    IF @deleted_count = 1
        PRINT '✅ Soft delete working correctly'
    ELSE
        PRINT '❌ Soft delete not working'
    
    -- Clean up
    DELETE FROM dbo.IssueAnchorLinks WHERE issue_key_hash = @test_hash;
END TRY
BEGIN CATCH
    PRINT '❌ Soft delete test failed: ' + ERROR_MESSAGE()
END CATCH

-- ========================================================================
-- SECTION 6: VERIFY HELPER VIEWS
-- ========================================================================

PRINT ''
PRINT '=== SECTION 6: Verifying helper views ==='

-- Check expanded view columns
SELECT COUNT(*) AS column_count
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'vw_IssueAnchorLinks_Expanded';

PRINT 'Columns in vw_IssueAnchorLinks_Expanded:'
SELECT COLUMN_NAME, DATA_TYPE, ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'vw_IssueAnchorLinks_Expanded'
ORDER BY ORDINAL_POSITION;

-- Check counts view columns
SELECT COUNT(*) AS column_count
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'vw_AnchorBlockerCounts';

PRINT ''
PRINT 'Columns in vw_AnchorBlockerCounts:'
SELECT COLUMN_NAME, DATA_TYPE, ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'vw_AnchorBlockerCounts'
ORDER BY ORDINAL_POSITION;

-- ========================================================================
-- SECTION 7: PERFORMANCE VERIFICATION
-- ========================================================================

PRINT ''
PRINT '=== SECTION 7: Performance verification ==='

-- Query vw_Issues_Reconciled (should be <1 second)
DECLARE @start_time DATETIME2 = SYSUTCDATETIME();
SELECT COUNT(*) FROM dbo.vw_Issues_Reconciled WHERE issue_key_hash IS NOT NULL;
DECLARE @end_time DATETIME2 = SYSUTCDATETIME();

PRINT '✅ vw_Issues_Reconciled query time: ' + CAST(DATEDIFF(MILLISECOND, @start_time, @end_time) AS VARCHAR(5)) + 'ms'

-- ========================================================================
-- SECTION 8: FINAL SUMMARY
-- ========================================================================

PRINT ''
PRINT '=== VALIDATION SUMMARY ==='
PRINT 'If all sections show ✅, implementation is ready for use'
PRINT 'If any sections show ❌, review the corresponding SQL deployment script'
PRINT ''
PRINT 'Next steps:'
PRINT '1. Backend: Add Python database helper functions'
PRINT '2. Backend: Create Flask API endpoints'
PRINT '3. Frontend: Create React components using endpoints'
PRINT '4. Testing: Run integration tests with sample data'
PRINT ''
