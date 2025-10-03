-- =====================================================================
-- Migration: Add CASCADE Constraints to Foreign Keys
-- Purpose: Enforce referential integrity at database level
-- Date: 2025-10-03
-- Risk: MEDIUM - Schema changes, requires backup
-- Rollback: See 001_rollback_cascade_constraints.sql
-- =====================================================================

-- IMPORTANT: Create full database backup before running!
-- BACKUP DATABASE ProjectManagement TO DISK='backup_pre_cascade_constraints.bak';

BEGIN TRANSACTION;

PRINT 'Starting CASCADE constraint migration...';
PRINT '========================================';

-- =====================================================================
-- PHASE 1: Drop existing FK constraints without CASCADE
-- =====================================================================

PRINT '';
PRINT 'PHASE 1: Dropping existing FK constraints...';

-- ProjectServices
IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ProjectServices_Projects')
BEGIN
    PRINT '  - Dropping FK_ProjectServices_Projects';
    ALTER TABLE ProjectServices DROP CONSTRAINT FK_ProjectServices_Projects;
END

-- ReviewSchedule (multiple FKs)
IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ReviewSchedule_Projects')
BEGIN
    PRINT '  - Dropping FK_ReviewSchedule_Projects';
    ALTER TABLE ReviewSchedule DROP CONSTRAINT FK_ReviewSchedule_Projects;
END

IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ReviewSchedule_Parameters')
BEGIN
    PRINT '  - Dropping FK_ReviewSchedule_Parameters';
    ALTER TABLE ReviewSchedule DROP CONSTRAINT FK_ReviewSchedule_Parameters;
END

IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ReviewSchedule_Users')
BEGIN
    PRINT '  - Dropping FK_ReviewSchedule_Users';
    ALTER TABLE ReviewSchedule DROP CONSTRAINT FK_ReviewSchedule_Users;
END

-- =====================================================================
-- PHASE 2: Add FK constraints WITH CASCADE
-- =====================================================================

PRINT '';
PRINT 'PHASE 2: Adding CASCADE constraints...';

-- ProjectServices → Projects
PRINT '  - Adding FK_ProjectServices_Projects WITH CASCADE';
ALTER TABLE ProjectServices
ADD CONSTRAINT FK_ProjectServices_Projects 
    FOREIGN KEY (project_id) 
    REFERENCES Projects(project_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE;

-- BillingClaims → Projects (NEW - was missing)
IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_BillingClaims_Projects')
BEGIN
    PRINT '  - Adding FK_BillingClaims_Projects WITH CASCADE';
    ALTER TABLE BillingClaims
    ADD CONSTRAINT FK_BillingClaims_Projects 
        FOREIGN KEY (project_id) 
        REFERENCES Projects(project_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE;
END

-- Tasks → Projects (NEW - was missing)
IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_Tasks_Projects')
BEGIN
    PRINT '  - Adding FK_Tasks_Projects WITH CASCADE';
    ALTER TABLE Tasks
    ADD CONSTRAINT FK_Tasks_Projects 
        FOREIGN KEY (project_id) 
        REFERENCES Projects(project_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE;
END

-- ACCImportFolders → Projects (NEW - was missing)
IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ACCImportFolders_Projects')
BEGIN
    PRINT '  - Adding FK_ACCImportFolders_Projects WITH CASCADE';
    ALTER TABLE ACCImportFolders
    ADD CONSTRAINT FK_ACCImportFolders_Projects 
        FOREIGN KEY (project_id) 
        REFERENCES Projects(project_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE;
END

-- ACCImportLogs → Projects (NEW - was missing)
IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ACCImportLogs_Projects')
BEGIN
    PRINT '  - Adding FK_ACCImportLogs_Projects WITH CASCADE';
    ALTER TABLE ACCImportLogs
    ADD CONSTRAINT FK_ACCImportLogs_Projects 
        FOREIGN KEY (project_id) 
        REFERENCES Projects(project_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE;
END

-- tblACCDocs → Projects (NEW - was missing)
IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_tblACCDocs_Projects')
BEGIN
    PRINT '  - Adding FK_tblACCDocs_Projects WITH CASCADE';
    ALTER TABLE tblACCDocs
    ADD CONSTRAINT FK_tblACCDocs_Projects 
        FOREIGN KEY (project_id) 
        REFERENCES Projects(project_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE;
END

-- ProjectBookmarks → Projects (NEW - was missing)
IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ProjectBookmarks_Projects')
BEGIN
    PRINT '  - Adding FK_ProjectBookmarks_Projects WITH CASCADE';
    ALTER TABLE ProjectBookmarks
    ADD CONSTRAINT FK_ProjectBookmarks_Projects 
        FOREIGN KEY (project_id) 
        REFERENCES Projects(project_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE;
END

-- ProjectBEPSections → Projects (NEW - was missing)
IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ProjectBEPSections_Projects')
BEGIN
    PRINT '  - Adding FK_ProjectBEPSections_Projects WITH CASCADE';
    ALTER TABLE ProjectBEPSections
    ADD CONSTRAINT FK_ProjectBEPSections_Projects 
        FOREIGN KEY (project_id) 
        REFERENCES Projects(project_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE;
END

-- ProjectHolds → Projects (NEW - was missing)
IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ProjectHolds_Projects')
BEGIN
    PRINT '  - Adding FK_ProjectHolds_Projects WITH CASCADE';
    ALTER TABLE ProjectHolds
    ADD CONSTRAINT FK_ProjectHolds_Projects 
        FOREIGN KEY (project_id) 
        REFERENCES Projects(project_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE;
END

-- ReviewParameters → Projects (NEW - was missing, column name inconsistency!)
-- Note: Column is 'ProjectID' (capital ID), not 'project_id'
IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ReviewParameters_Projects')
BEGIN
    PRINT '  - Adding FK_ReviewParameters_Projects WITH CASCADE';
    ALTER TABLE ReviewParameters
    ADD CONSTRAINT FK_ReviewParameters_Projects 
        FOREIGN KEY (ProjectID) 
        REFERENCES Projects(project_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE;
END

-- ReviewSchedule → Projects (re-add with CASCADE)
PRINT '  - Adding FK_ReviewSchedule_Projects WITH CASCADE';
ALTER TABLE ReviewSchedule
ADD CONSTRAINT FK_ReviewSchedule_Projects 
    FOREIGN KEY (project_id) 
    REFERENCES Projects(project_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE;

-- ReviewSchedule → ReviewParameters (composite FK - NO CASCADE, referenced table has CASCADE)
PRINT '  - Adding FK_ReviewSchedule_Parameters (no CASCADE)';
ALTER TABLE ReviewSchedule
ADD CONSTRAINT FK_ReviewSchedule_Parameters 
    FOREIGN KEY (cycle_id, project_id) 
    REFERENCES ReviewParameters(cycle_id, ProjectID);

-- ReviewSchedule → Users (NO CASCADE - preserve user records)
PRINT '  - Adding FK_ReviewSchedule_Users (no CASCADE)';
ALTER TABLE ReviewSchedule
ADD CONSTRAINT FK_ReviewSchedule_Users 
    FOREIGN KEY (assigned_to) 
    REFERENCES users(user_id);

-- ReviewSchedules → Projects (different table, NEW)
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'ReviewSchedules')
BEGIN
    IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ReviewSchedules_Projects')
    BEGIN
        PRINT '  - Adding FK_ReviewSchedules_Projects WITH CASCADE';
        ALTER TABLE ReviewSchedules
        ADD CONSTRAINT FK_ReviewSchedules_Projects 
            FOREIGN KEY (project_id) 
            REFERENCES Projects(project_id)
            ON DELETE CASCADE
            ON UPDATE CASCADE;
    END
END

-- ReviewCycleDetails → Projects (NEW)
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'ReviewCycleDetails')
BEGIN
    IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ReviewCycleDetails_Projects')
    BEGIN
        PRINT '  - Adding FK_ReviewCycleDetails_Projects WITH CASCADE';
        ALTER TABLE ReviewCycleDetails
        ADD CONSTRAINT FK_ReviewCycleDetails_Projects 
            FOREIGN KEY (project_id) 
            REFERENCES Projects(project_id)
            ON DELETE CASCADE
            ON UPDATE CASCADE;
    END
END

-- ReviewStages → Projects (NEW)
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'ReviewStages')
BEGIN
    IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ReviewStages_Projects')
    BEGIN
        PRINT '  - Adding FK_ReviewStages_Projects WITH CASCADE';
        ALTER TABLE ReviewStages
        ADD CONSTRAINT FK_ReviewStages_Projects 
            FOREIGN KEY (project_id) 
            REFERENCES Projects(project_id)
            ON DELETE CASCADE
            ON UPDATE CASCADE;
    END
END

-- ProjectReviews → Projects (NEW)
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'ProjectReviews')
BEGIN
    IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ProjectReviews_Projects')
    BEGIN
        PRINT '  - Adding FK_ProjectReviews_Projects WITH CASCADE';
        ALTER TABLE ProjectReviews
        ADD CONSTRAINT FK_ProjectReviews_Projects 
            FOREIGN KEY (project_id) 
            REFERENCES Projects(project_id)
            ON DELETE CASCADE
            ON UPDATE CASCADE;
    END
END

-- ProjectReviewCycles → Projects (NEW)
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'ProjectReviewCycles')
BEGIN
    IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ProjectReviewCycles_Projects')
    BEGIN
        PRINT '  - Adding FK_ProjectReviewCycles_Projects WITH CASCADE';
        ALTER TABLE ProjectReviewCycles
        ADD CONSTRAINT FK_ProjectReviewCycles_Projects 
            FOREIGN KEY (project_id) 
            REFERENCES Projects(project_id)
            ON DELETE CASCADE
            ON UPDATE CASCADE;
    END
END

-- ContractualLinks → Projects (NEW)
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'ContractualLinks')
BEGIN
    IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ContractualLinks_Projects')
    BEGIN
        PRINT '  - Adding FK_ContractualLinks_Projects WITH CASCADE';
        ALTER TABLE ContractualLinks
        ADD CONSTRAINT FK_ContractualLinks_Projects 
            FOREIGN KEY (project_id) 
            REFERENCES Projects(project_id)
            ON DELETE CASCADE
            ON UPDATE CASCADE;
    END
END

-- BEPApprovals → Projects (NEW)
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'bep_approvals')
BEGIN
    IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_BEPApprovals_Projects')
    BEGIN
        PRINT '  - Adding FK_BEPApprovals_Projects WITH CASCADE';
        ALTER TABLE bep_approvals
        ADD CONSTRAINT FK_BEPApprovals_Projects 
            FOREIGN KEY (project_id) 
            REFERENCES Projects(project_id)
            ON DELETE CASCADE
            ON UPDATE CASCADE;
    END
END

-- =====================================================================
-- PHASE 3: Add indexes for performance
-- =====================================================================

PRINT '';
PRINT 'PHASE 3: Adding indexes for FK performance...';

-- Index on ProjectServices.project_id (if not exists)
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_ProjectServices_ProjectID')
BEGIN
    PRINT '  - Creating IX_ProjectServices_ProjectID';
    CREATE NONCLUSTERED INDEX IX_ProjectServices_ProjectID 
    ON ProjectServices(project_id);
END

-- Index on Tasks.project_id (if not exists)
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Tasks_ProjectID')
BEGIN
    PRINT '  - Creating IX_Tasks_ProjectID';
    CREATE NONCLUSTERED INDEX IX_Tasks_ProjectID 
    ON Tasks(project_id);
END

-- Index on BillingClaims.project_id (if not exists)
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_BillingClaims_ProjectID')
BEGIN
    PRINT '  - Creating IX_BillingClaims_ProjectID';
    CREATE NONCLUSTERED INDEX IX_BillingClaims_ProjectID 
    ON BillingClaims(project_id);
END

-- =====================================================================
-- PHASE 4: Validation
-- =====================================================================

PRINT '';
PRINT 'PHASE 4: Validating constraints...';

DECLARE @fk_count INT;
SELECT @fk_count = COUNT(*)
FROM sys.foreign_keys fk
INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
INNER JOIN sys.columns c ON fkc.parent_object_id = c.object_id AND fkc.parent_column_id = c.column_id
WHERE c.name IN ('project_id', 'ProjectID')
    AND fk.referenced_object_id = OBJECT_ID('Projects');

PRINT '  - Total FK constraints referencing Projects: ' + CAST(@fk_count AS NVARCHAR(10));

DECLARE @cascade_count INT;
SELECT @cascade_count = COUNT(*)
FROM sys.foreign_keys
WHERE referenced_object_id = OBJECT_ID('Projects')
    AND delete_referential_action = 1;  -- CASCADE

PRINT '  - FK constraints with ON DELETE CASCADE: ' + CAST(@cascade_count AS NVARCHAR(10));

-- =====================================================================
-- COMMIT or ROLLBACK
-- =====================================================================

-- Uncomment one of the following:

-- COMMIT TRANSACTION;
-- PRINT '';
-- PRINT '✅ SUCCESS: CASCADE constraints migration completed!';
-- PRINT 'To test, try: DELETE FROM Projects WHERE project_id = <test_id>';

ROLLBACK TRANSACTION;
PRINT '';
PRINT '⚠️  ROLLED BACK: Review the output above, then change ROLLBACK to COMMIT';
PRINT '';
PRINT 'Next steps:';
PRINT '1. Review all FK constraints added';
PRINT '2. Test in non-production environment';
PRINT '3. Change ROLLBACK to COMMIT';
PRINT '4. Re-run this script';

GO

-- =====================================================================
-- Verification Queries (run after COMMIT)
-- =====================================================================

/*
-- Check all FK constraints on Projects
SELECT 
    fk.name AS FK_Name,
    OBJECT_NAME(fk.parent_object_id) AS Table_Name,
    COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS Column_Name,
    fk.delete_referential_action_desc AS Delete_Action,
    fk.update_referential_action_desc AS Update_Action
FROM sys.foreign_keys fk
INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
WHERE fk.referenced_object_id = OBJECT_ID('Projects')
ORDER BY Table_Name;

-- Test CASCADE delete (use a test project!)
-- DELETE FROM Projects WHERE project_id = 999;  -- Replace with test ID

-- Check for orphaned records (should return 0 rows)
SELECT ps.* 
FROM ProjectServices ps
LEFT JOIN Projects p ON ps.project_id = p.project_id
WHERE p.project_id IS NULL;
*/
