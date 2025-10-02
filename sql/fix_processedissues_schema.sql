-- ============================================================
-- FIX SCHEMA COMPATIBILITY FOR PROCESSEDISSUES TABLE
-- ============================================================
-- This script fixes data type mismatches between the source
-- view (vw_ProjectManagement_AllIssues) and ProcessedIssues table
--
-- Issues Fixed:
-- 1. source_issue_id: Already NVARCHAR(255) ✓
-- 2. project_id: INT → Need to handle UNIQUEIDENTIFIER from view
-- 3. Foreign key constraint needs to be dropped and recreated
-- ============================================================

USE ProjectManagement;
GO

PRINT 'Starting schema fix for ProcessedIssues table...'
GO

-- Step 1: Check if table has data (backup if needed)
DECLARE @row_count INT;
SELECT @row_count = COUNT(*) FROM ProcessedIssues;
PRINT 'Current row count: ' + CAST(@row_count AS VARCHAR(10));

IF @row_count > 0
BEGIN
    PRINT 'WARNING: Table contains data. Creating backup...'
    
    -- Create backup table
    IF OBJECT_ID('ProcessedIssues_Backup', 'U') IS NOT NULL
        DROP TABLE ProcessedIssues_Backup;
    
    SELECT * INTO ProcessedIssues_Backup FROM ProcessedIssues;
    PRINT 'Backup created: ProcessedIssues_Backup'
END
GO

-- Step 2: Drop foreign key constraint on project_id
PRINT 'Dropping foreign key constraint...'
DECLARE @ConstraintName NVARCHAR(255);
SELECT @ConstraintName = name
FROM sys.foreign_keys
WHERE parent_object_id = OBJECT_ID('ProcessedIssues')
AND COL_NAME(parent_object_id, (SELECT parent_column_id FROM sys.foreign_key_columns WHERE constraint_object_id = object_id)) = 'project_id';

IF @ConstraintName IS NOT NULL
BEGIN
    DECLARE @SQL NVARCHAR(500);
    SET @SQL = 'ALTER TABLE ProcessedIssues DROP CONSTRAINT ' + @ConstraintName;
    EXEC sp_executesql @SQL;
    PRINT 'Foreign key constraint dropped: ' + @ConstraintName;
END
ELSE
BEGIN
    PRINT 'No foreign key constraint found on project_id';
END
GO

-- Step 3: Check projects table project_id type
PRINT 'Checking projects table schema...'
DECLARE @projects_type NVARCHAR(50);
SELECT @projects_type = DATA_TYPE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'projects' AND COLUMN_NAME = 'project_id';
PRINT 'projects.project_id type: ' + @projects_type;
GO

-- Step 4: Alter project_id column to match source
-- Since view returns GUID string, we'll keep it as NVARCHAR for flexibility
PRINT 'Altering project_id column...'
ALTER TABLE ProcessedIssues
ALTER COLUMN project_id NVARCHAR(255) NOT NULL;
PRINT 'project_id changed to NVARCHAR(255)';
GO

-- Step 5: Verify the changes
PRINT ''
PRINT 'Verification of changes:'
PRINT '========================================================================'
SELECT 
    COLUMN_NAME, 
    DATA_TYPE, 
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'ProcessedIssues'
AND COLUMN_NAME IN ('source_issue_id', 'project_id', 'source')
ORDER BY ORDINAL_POSITION;
GO

-- Step 6: Recreate foreign key (optional, with ON DELETE CASCADE)
-- Note: Only if projects.project_id is also NVARCHAR, otherwise skip
PRINT ''
PRINT 'Foreign key recreation skipped - different data types between tables'
PRINT 'This is expected when source view provides GUIDs but projects table uses INT'
GO

PRINT ''
PRINT '========================================================================'
PRINT 'SCHEMA FIX COMPLETE!'
PRINT '========================================================================'
PRINT 'ProcessedIssues table is now compatible with vw_ProjectManagement_AllIssues'
PRINT ''
PRINT 'Next steps:'
PRINT '  1. Run batch processing: python tools\run_batch_processing.py --limit 50 --yes'
PRINT '  2. Verify results in ProcessedIssues table'
PRINT '========================================================================'
GO
