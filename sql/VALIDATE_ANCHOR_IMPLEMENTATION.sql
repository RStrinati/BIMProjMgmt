-- Comprehensive validation of anchor linking implementation
USE ProjectManagement;
GO

PRINT '====== VALIDATION RESULTS ======'
GO

-- 1. Check view has issue_key_hash
PRINT ''
PRINT '1. vw_Issues_Reconciled structure:'
SELECT COUNT(*) AS total_rows, COUNT(DISTINCT issue_key_hash) AS distinct_hashes
FROM dbo.vw_Issues_Reconciled
WHERE issue_key_hash IS NOT NULL;
GO

-- 2. Check table exists
PRINT ''
PRINT '2. IssueAnchorLinks table:'
SELECT
    CASE WHEN COUNT(*) = 1 THEN 'Exists' ELSE 'Not found' END AS status
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_NAME = 'IssueAnchorLinks' AND TABLE_SCHEMA = 'dbo';
GO

-- 3. Check views exist
PRINT ''
PRINT '3. Helper views:'
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME IN ('vw_IssueAnchorLinks_Expanded', 'vw_AnchorBlockerCounts')
AND TABLE_SCHEMA = 'dbo'
ORDER BY TABLE_NAME;
GO

-- 4. Test insert to IssueAnchorLinks
PRINT ''
PRINT '4. Testing IssueAnchorLinks insert:'
DECLARE @test_hash VARBINARY(32)
SELECT TOP 1 @test_hash = issue_key_hash FROM dbo.vw_Issues_Reconciled WHERE issue_key_hash IS NOT NULL
IF @test_hash IS NOT NULL
BEGIN
    INSERT INTO dbo.IssueAnchorLinks (project_id, issue_key_hash, anchor_type, service_id, link_role)
    VALUES (1, @test_hash, 'service', 999, 'blocks')
    SELECT 'Insert successful - constraint check passed' AS status
    DELETE FROM dbo.IssueAnchorLinks WHERE service_id = 999
END
ELSE
BEGIN
    SELECT 'No test hash available' AS status
END
GO

-- 5. Index summary
PRINT ''
PRINT '5. Indexes on IssueAnchorLinks:'
SELECT name FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.IssueAnchorLinks') AND index_id > 0
ORDER BY name;
GO

-- 6. Sample view query
PRINT ''
PRINT '6. vw_IssueAnchorLinks_Expanded query (empty, no links yet):'
SELECT COUNT(*) AS link_count FROM dbo.vw_IssueAnchorLinks_Expanded;
GO

-- 7. Sample blocker counts view
PRINT ''
PRINT '7. vw_AnchorBlockerCounts query (empty, no links yet):'
SELECT COUNT(*) AS anchor_count FROM dbo.vw_AnchorBlockerCounts;
GO

-- 8. Performance check on main view
PRINT ''
PRINT '8. Performance check - vw_Issues_Reconciled query with hash filter:'
SET STATISTICS TIME ON
SELECT COUNT(*) FROM dbo.vw_Issues_Reconciled WHERE issue_key_hash IS NOT NULL
SET STATISTICS TIME OFF
GO

PRINT ''
PRINT '====== VALIDATION COMPLETE ======'
GO
