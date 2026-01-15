-- Analyze ACC Issue ID Mismatch: UUID vs Numeric
-- This query shows match rates between Issues_Current and acc_data_schema.dbo.issues_issues

USE ProjectManagement;
GO

PRINT '=== Match Rate Analysis ===';

-- Test 1: Join by UUID (source_issue_id as issue_id)
PRINT 'Test 1: Joining by UUID (source_issue_id = issue_id)';
DECLARE @total_acc_issues INT;
SELECT @total_acc_issues = COUNT(DISTINCT issue_key) FROM dbo.Issues_Current WHERE source_system='ACC';

SELECT 
    'Join by UUID' as join_type,
    COUNT(DISTINCT ic.issue_key) as matched_count,
    @total_acc_issues as total_acc_issues,
    CAST(
        100.0 * COUNT(DISTINCT ic.issue_key) / @total_acc_issues
        AS DECIMAL(5,2)
    ) as match_percentage
FROM dbo.Issues_Current ic
INNER JOIN acc_data_schema.dbo.issues_issues acc
    ON ic.source_issue_id = CAST(acc.issue_id AS NVARCHAR(MAX))
WHERE ic.source_system = 'ACC'
GO

-- Test 2: Join by numeric display_id (for numeric source_issue_ids only)
PRINT 'Test 2: Joining by numeric (source_issue_id as display_id, project matched)';
SELECT 
    'Join by numeric + project' as join_type,
    COUNT(DISTINCT ic.issue_key) as matched_count,
    @total_acc_issues as total_acc_issues,
    CAST(
        100.0 * COUNT(DISTINCT ic.issue_key) / @total_acc_issues
        AS DECIMAL(5,2)
    ) as match_percentage
FROM dbo.Issues_Current ic
INNER JOIN acc_data_schema.dbo.issues_issues acc
    ON TRY_CAST(ic.source_issue_id AS INT) = acc.display_id
    AND ic.source_project_id = CAST(acc.bim360_project_id AS NVARCHAR(100))
WHERE ic.source_system = 'ACC'
    AND ic.source_issue_id NOT LIKE '%-%'
GO

-- Test 3: Show example data - UUID matches
PRINT 'Test 3: Example UUID matches';
SELECT TOP 5
    ic.issue_key,
    ic.source_issue_id,
    CAST(acc.issue_id AS NVARCHAR(MAX)) as acc_issue_uuid,
    acc.display_id,
    ic.source_project_id,
    CAST(acc.bim360_project_id AS NVARCHAR(100)) as acc_project_id
FROM dbo.Issues_Current ic
INNER JOIN acc_data_schema.dbo.issues_issues acc
    ON ic.source_issue_id = CAST(acc.issue_id AS NVARCHAR(MAX))
WHERE ic.source_system = 'ACC'
ORDER BY ic.created_at DESC
GO

-- Test 4: Show example data - numeric matches
PRINT 'Test 4: Example numeric matches';
SELECT TOP 5
    ic.issue_key,
    ic.source_issue_id,
    CAST(acc.issue_id AS NVARCHAR(MAX)) as acc_issue_uuid,
    acc.display_id,
    ic.source_project_id,
    CAST(acc.bim360_project_id AS NVARCHAR(100)) as acc_project_id
FROM dbo.Issues_Current ic
INNER JOIN acc_data_schema.dbo.issues_issues acc
    ON TRY_CAST(ic.source_issue_id AS INT) = acc.display_id
    AND ic.source_project_id = CAST(acc.bim360_project_id AS NVARCHAR(100))
WHERE ic.source_system = 'ACC'
    AND ic.source_issue_id NOT LIKE '%-%'
ORDER BY ic.created_at DESC
GO

-- Test 5: Show distribution
PRINT 'Test 5: Distribution of source_issue_id formats';
SELECT 
    CASE 
        WHEN source_issue_id LIKE '%-%' THEN 'UUID-like' 
        ELSE 'Numeric-like' 
    END as id_type,
    COUNT(*) as count,
    CAST(100.0 * COUNT(*) / (SELECT COUNT(*) FROM dbo.Issues_Current WHERE source_system='ACC') AS DECIMAL(5,2)) as pct
FROM dbo.Issues_Current
WHERE source_system = 'ACC'
GROUP BY CASE WHEN source_issue_id LIKE '%-%' THEN 'UUID-like' ELSE 'Numeric-like' END
GO

-- Test 6: Show unmatchable issues (those that don't join well)
PRINT 'Test 6: Issues that may have join issues';
SELECT TOP 20
    ic.issue_key,
    ic.source_issue_id,
    ic.source_project_id
FROM dbo.Issues_Current ic
LEFT JOIN acc_data_schema.dbo.issues_issues acc_uuid
    ON ic.source_issue_id = CAST(acc_uuid.issue_id AS NVARCHAR(MAX))
LEFT JOIN acc_data_schema.dbo.issues_issues acc_numeric
    ON TRY_CAST(ic.source_issue_id AS INT) = acc_numeric.display_id
    AND ic.source_project_id = CAST(acc_numeric.bim360_project_id AS NVARCHAR(100))
WHERE ic.source_system = 'ACC'
    AND acc_uuid.issue_id IS NULL
    AND acc_numeric.issue_id IS NULL
ORDER BY ic.created_at DESC
GO
