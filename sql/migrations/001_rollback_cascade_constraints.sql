-- =====================================================================
-- Rollback Migration: Remove CASCADE Constraints from Foreign Keys
-- Purpose: Restore original FK constraints without CASCADE
-- Date: 2025-10-03
-- Use: If 001_add_cascade_constraints.sql causes issues
-- =====================================================================

BEGIN TRANSACTION;

PRINT 'Starting CASCADE constraint rollback...';
PRINT '========================================';

-- =====================================================================
-- PHASE 1: Drop FK constraints WITH CASCADE
-- =====================================================================

PRINT '';
PRINT 'PHASE 1: Dropping CASCADE constraints...';

-- Drop all FK constraints we added
IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ProjectServices_Projects')
BEGIN
    PRINT '  - Dropping FK_ProjectServices_Projects';
    ALTER TABLE ProjectServices DROP CONSTRAINT FK_ProjectServices_Projects;
END

IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_BillingClaims_Projects')
BEGIN
    PRINT '  - Dropping FK_BillingClaims_Projects';
    ALTER TABLE BillingClaims DROP CONSTRAINT FK_BillingClaims_Projects;
END

IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_Tasks_Projects')
BEGIN
    PRINT '  - Dropping FK_Tasks_Projects';
    ALTER TABLE Tasks DROP CONSTRAINT FK_Tasks_Projects;
END

IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ACCImportFolders_Projects')
BEGIN
    PRINT '  - Dropping FK_ACCImportFolders_Projects';
    ALTER TABLE ACCImportFolders DROP CONSTRAINT FK_ACCImportFolders_Projects;
END

IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ACCImportLogs_Projects')
BEGIN
    PRINT '  - Dropping FK_ACCImportLogs_Projects';
    ALTER TABLE ACCImportLogs DROP CONSTRAINT FK_ACCImportLogs_Projects;
END

IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_tblACCDocs_Projects')
BEGIN
    PRINT '  - Dropping FK_tblACCDocs_Projects';
    ALTER TABLE tblACCDocs DROP CONSTRAINT FK_tblACCDocs_Projects;
END

IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ProjectBookmarks_Projects')
BEGIN
    PRINT '  - Dropping FK_ProjectBookmarks_Projects';
    ALTER TABLE ProjectBookmarks DROP CONSTRAINT FK_ProjectBookmarks_Projects;
END

IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ProjectBEPSections_Projects')
BEGIN
    PRINT '  - Dropping FK_ProjectBEPSections_Projects';
    ALTER TABLE ProjectBEPSections DROP CONSTRAINT FK_ProjectBEPSections_Projects;
END

IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ProjectHolds_Projects')
BEGIN
    PRINT '  - Dropping FK_ProjectHolds_Projects';
    ALTER TABLE ProjectHolds DROP CONSTRAINT FK_ProjectHolds_Projects;
END

IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ReviewParameters_Projects')
BEGIN
    PRINT '  - Dropping FK_ReviewParameters_Projects';
    ALTER TABLE ReviewParameters DROP CONSTRAINT FK_ReviewParameters_Projects;
END

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

IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ReviewSchedules_Projects')
BEGIN
    PRINT '  - Dropping FK_ReviewSchedules_Projects';
    ALTER TABLE ReviewSchedules DROP CONSTRAINT FK_ReviewSchedules_Projects;
END

IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ReviewCycleDetails_Projects')
BEGIN
    PRINT '  - Dropping FK_ReviewCycleDetails_Projects';
    ALTER TABLE ReviewCycleDetails DROP CONSTRAINT FK_ReviewCycleDetails_Projects;
END

IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ReviewStages_Projects')
BEGIN
    PRINT '  - Dropping FK_ReviewStages_Projects';
    ALTER TABLE ReviewStages DROP CONSTRAINT FK_ReviewStages_Projects;
END

IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ProjectReviews_Projects')
BEGIN
    PRINT '  - Dropping FK_ProjectReviews_Projects';
    ALTER TABLE ProjectReviews DROP CONSTRAINT FK_ProjectReviews_Projects;
END

IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ProjectReviewCycles_Projects')
BEGIN
    PRINT '  - Dropping FK_ProjectReviewCycles_Projects';
    ALTER TABLE ProjectReviewCycles DROP CONSTRAINT FK_ProjectReviewCycles_Projects;
END

IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ContractualLinks_Projects')
BEGIN
    PRINT '  - Dropping FK_ContractualLinks_Projects';
    ALTER TABLE ContractualLinks DROP CONSTRAINT FK_ContractualLinks_Projects;
END

IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_BEPApprovals_Projects')
BEGIN
    PRINT '  - Dropping FK_BEPApprovals_Projects';
    ALTER TABLE bep_approvals DROP CONSTRAINT FK_BEPApprovals_Projects;
END

-- =====================================================================
-- PHASE 2: Re-add original FK constraints WITHOUT CASCADE
-- =====================================================================

PRINT '';
PRINT 'PHASE 2: Re-adding original FK constraints (no CASCADE)...';

-- ProjectServices → Projects (original)
PRINT '  - Adding FK_ProjectServices_Projects';
ALTER TABLE ProjectServices
ADD CONSTRAINT FK_ProjectServices_Projects 
    FOREIGN KEY (project_id) 
    REFERENCES Projects(project_id);

-- ReviewSchedule → Projects (original)
PRINT '  - Adding FK_ReviewSchedule_Projects';
ALTER TABLE ReviewSchedule
ADD CONSTRAINT FK_ReviewSchedule_Projects 
    FOREIGN KEY (project_id) 
    REFERENCES Projects(project_id);

-- ReviewSchedule → ReviewParameters (original)
PRINT '  - Adding FK_ReviewSchedule_Parameters';
ALTER TABLE ReviewSchedule
ADD CONSTRAINT FK_ReviewSchedule_Parameters 
    FOREIGN KEY (cycle_id, project_id) 
    REFERENCES ReviewParameters(cycle_id, ProjectID);

-- ReviewSchedule → Users (original)
PRINT '  - Adding FK_ReviewSchedule_Users';
ALTER TABLE ReviewSchedule
ADD CONSTRAINT FK_ReviewSchedule_Users 
    FOREIGN KEY (assigned_to) 
    REFERENCES users(user_id);

-- Note: Only re-adding constraints that existed before migration
-- Other tables may not have had FK constraints originally

-- =====================================================================
-- PHASE 3: Validation
-- =====================================================================

PRINT '';
PRINT 'PHASE 3: Validating rollback...';

DECLARE @cascade_count INT;
SELECT @cascade_count = COUNT(*)
FROM sys.foreign_keys
WHERE referenced_object_id = OBJECT_ID('Projects')
    AND delete_referential_action = 1;  -- CASCADE

PRINT '  - FK constraints with ON DELETE CASCADE: ' + CAST(@cascade_count AS NVARCHAR(10));
PRINT '    (Should be 0 after rollback)';

-- =====================================================================
-- COMMIT or ROLLBACK
-- =====================================================================

-- Uncomment one of the following:

-- COMMIT TRANSACTION;
-- PRINT '';
-- PRINT '✅ SUCCESS: Rollback completed - original constraints restored';

ROLLBACK TRANSACTION;
PRINT '';
PRINT '⚠️  ROLLED BACK: Review the output above, then change ROLLBACK to COMMIT';
PRINT '';
PRINT 'WARNING: After rollback, delete_project() will use manual CASCADE deletes';
PRINT 'WARNING: Direct SQL project deletion will leave orphaned records!';

GO
