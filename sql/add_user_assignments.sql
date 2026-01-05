-- =====================================================================
-- User Assignment Enhancement for Services, Reviews, and Items
-- =====================================================================
-- This migration adds user assignment capabilities to the project
-- management system, enabling assignment of services, reviews, and
-- items to specific users while maintaining project lead as default.
-- =====================================================================

USE ProjectManagement;
GO

-- =====================================================================
-- 1. Add assigned_user_id to ProjectServices
-- =====================================================================
IF NOT EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE object_id = OBJECT_ID('dbo.ProjectServices') 
    AND name = 'assigned_user_id'
)
BEGIN
    ALTER TABLE dbo.ProjectServices
    ADD assigned_user_id INT NULL;
    
    PRINT 'Added assigned_user_id column to ProjectServices table';
END
ELSE
BEGIN
    PRINT 'assigned_user_id column already exists in ProjectServices table';
END
GO

-- Add foreign key constraint to users table
IF NOT EXISTS (
    SELECT 1 FROM sys.foreign_keys 
    WHERE name = 'FK_ProjectServices_AssignedUser'
)
BEGIN
    ALTER TABLE dbo.ProjectServices
    ADD CONSTRAINT FK_ProjectServices_AssignedUser
    FOREIGN KEY (assigned_user_id) REFERENCES dbo.users(user_id)
    ON DELETE SET NULL;
    
    PRINT 'Added FK_ProjectServices_AssignedUser foreign key constraint';
END
GO

-- =====================================================================
-- 2. Add assigned_user_id to ServiceReviews
-- =====================================================================
IF NOT EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE object_id = OBJECT_ID('dbo.ServiceReviews') 
    AND name = 'assigned_user_id'
)
BEGIN
    ALTER TABLE dbo.ServiceReviews
    ADD assigned_user_id INT NULL;
    
    PRINT 'Added assigned_user_id column to ServiceReviews table';
END
ELSE
BEGIN
    PRINT 'assigned_user_id column already exists in ServiceReviews table';
END
GO

-- Add foreign key constraint to users table
IF NOT EXISTS (
    SELECT 1 FROM sys.foreign_keys 
    WHERE name = 'FK_ServiceReviews_AssignedUser'
)
BEGIN
    ALTER TABLE dbo.ServiceReviews
    ADD CONSTRAINT FK_ServiceReviews_AssignedUser
    FOREIGN KEY (assigned_user_id) REFERENCES dbo.users(user_id)
    ON DELETE SET NULL;
    
    PRINT 'Added FK_ServiceReviews_AssignedUser foreign key constraint';
END
GO

-- =====================================================================
-- 3. Add assigned_user_id to ServiceItems (if table exists)
-- =====================================================================
IF OBJECT_ID('dbo.ServiceItems', 'U') IS NOT NULL
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM sys.columns 
        WHERE object_id = OBJECT_ID('dbo.ServiceItems') 
        AND name = 'assigned_user_id'
    )
    BEGIN
        ALTER TABLE dbo.ServiceItems
        ADD assigned_user_id INT NULL;
        
        PRINT 'Added assigned_user_id column to ServiceItems table';
    END
    ELSE
    BEGIN
        PRINT 'assigned_user_id column already exists in ServiceItems table';
    END

    -- Add foreign key constraint to users table
    IF NOT EXISTS (
        SELECT 1 FROM sys.foreign_keys 
        WHERE name = 'FK_ServiceItems_AssignedUser'
    )
    BEGIN
        ALTER TABLE dbo.ServiceItems
        ADD CONSTRAINT FK_ServiceItems_AssignedUser
        FOREIGN KEY (assigned_user_id) REFERENCES dbo.users(user_id)
        ON DELETE SET NULL;
        
        PRINT 'Added FK_ServiceItems_AssignedUser foreign key constraint';
    END
END
ELSE
BEGIN
    PRINT 'ServiceItems table does not exist - skipping';
END
GO

-- =====================================================================
-- 4. Update existing records with project lead as default assignee
-- =====================================================================
-- This sets the project's internal_lead as the default assignee for
-- all existing services and reviews that don't have an assigned user.
-- =====================================================================

PRINT 'Updating existing ProjectServices with project lead as default assignee...';
UPDATE ps
SET ps.assigned_user_id = u.user_id
FROM dbo.ProjectServices ps
INNER JOIN dbo.projects p ON ps.project_id = p.project_id
INNER JOIN dbo.users u ON p.internal_lead = u.name
WHERE ps.assigned_user_id IS NULL
  AND p.internal_lead IS NOT NULL;

DECLARE @ServicesUpdated INT = @@ROWCOUNT;
PRINT CONCAT('Updated ', @ServicesUpdated, ' services with project lead assignment');
GO

PRINT 'Updating existing ServiceReviews with project lead as default assignee...';
UPDATE sr
SET sr.assigned_user_id = u.user_id
FROM dbo.ServiceReviews sr
INNER JOIN dbo.ProjectServices ps ON sr.service_id = ps.service_id
INNER JOIN dbo.projects p ON ps.project_id = p.project_id
INNER JOIN dbo.users u ON p.internal_lead = u.name
WHERE sr.assigned_user_id IS NULL
  AND p.internal_lead IS NOT NULL;

DECLARE @ReviewsUpdated INT = @@ROWCOUNT;
PRINT CONCAT('Updated ', @ReviewsUpdated, ' reviews with project lead assignment');
GO

-- =====================================================================
-- 5. Create helper view for user workload analysis
-- =====================================================================
IF OBJECT_ID('dbo.vw_user_workload', 'V') IS NOT NULL
    DROP VIEW dbo.vw_user_workload;
GO

CREATE VIEW dbo.vw_user_workload AS
SELECT 
    u.user_id,
    u.name AS user_name,
    u.email AS user_email,
    u.role AS user_role,
    
    -- Service assignments
    COUNT(DISTINCT ps.service_id) AS assigned_services_count,
    
    -- Review assignments
    COUNT(DISTINCT sr.review_id) AS assigned_reviews_count,
    
    -- Active reviews (not completed or cancelled)
    SUM(CASE 
        WHEN sr.status NOT IN ('completed', 'cancelled') 
        THEN 1 ELSE 0 
    END) AS active_reviews_count,
    
    -- Overdue reviews
    SUM(CASE 
        WHEN sr.status NOT IN ('completed', 'cancelled') 
        AND sr.due_date < GETDATE() 
        THEN 1 ELSE 0 
    END) AS overdue_reviews_count,
    
    -- Projects involved in
    COUNT(DISTINCT ps.project_id) AS projects_count

FROM dbo.users u
LEFT JOIN dbo.ProjectServices ps ON u.user_id = ps.assigned_user_id
LEFT JOIN dbo.ServiceReviews sr ON u.user_id = sr.assigned_user_id
GROUP BY u.user_id, u.name, u.email, u.role;
GO

PRINT 'Created vw_user_workload view for workload analysis';
GO

-- =====================================================================
-- 6. Create helper function to get effective assignee
-- =====================================================================
-- This function returns the assigned user ID, defaulting to the
-- project lead if no specific assignee is set.
-- =====================================================================
IF OBJECT_ID('dbo.fn_get_effective_assignee', 'FN') IS NOT NULL
    DROP FUNCTION dbo.fn_get_effective_assignee;
GO

CREATE FUNCTION dbo.fn_get_effective_assignee
(
    @project_id INT,
    @assigned_user_id INT = NULL
)
RETURNS INT
AS
BEGIN
    DECLARE @effective_user_id INT;
    
    -- If explicitly assigned, use that
    IF @assigned_user_id IS NOT NULL
    BEGIN
        SET @effective_user_id = @assigned_user_id;
    END
    ELSE
    BEGIN
        -- Otherwise, get project lead
        SELECT @effective_user_id = u.user_id
        FROM dbo.projects p
        INNER JOIN dbo.users u ON p.internal_lead = u.name
        WHERE p.project_id = @project_id;
    END
    
    RETURN @effective_user_id;
END;
GO

PRINT 'Created fn_get_effective_assignee function';
GO

-- =====================================================================
-- 7. Create audit trigger for assignment changes
-- =====================================================================
IF OBJECT_ID('dbo.tr_ProjectServices_AssignmentAudit', 'TR') IS NOT NULL
    DROP TRIGGER dbo.tr_ProjectServices_AssignmentAudit;
GO

CREATE TRIGGER dbo.tr_ProjectServices_AssignmentAudit
ON dbo.ProjectServices
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only log if assigned_user_id changed
    IF UPDATE(assigned_user_id)
    BEGIN
        INSERT INTO dbo.audit_log (table_name, record_id, action, old_value, new_value, changed_at)
        SELECT 
            'ProjectServices',
            i.service_id,
            'assignment_change',
            CAST(d.assigned_user_id AS NVARCHAR(50)),
            CAST(i.assigned_user_id AS NVARCHAR(50)),
            GETDATE()
        FROM inserted i
        INNER JOIN deleted d ON i.service_id = d.service_id
        WHERE ISNULL(i.assigned_user_id, -1) <> ISNULL(d.assigned_user_id, -1);
    END
END;
GO

PRINT 'Created tr_ProjectServices_AssignmentAudit trigger';
GO

-- =====================================================================
-- 8. Create audit_log table if it doesn't exist
-- =====================================================================
IF OBJECT_ID('dbo.audit_log', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.audit_log (
        log_id INT IDENTITY(1,1) PRIMARY KEY,
        table_name NVARCHAR(128) NOT NULL,
        record_id INT NOT NULL,
        action NVARCHAR(50) NOT NULL,
        old_value NVARCHAR(MAX) NULL,
        new_value NVARCHAR(MAX) NULL,
        changed_at DATETIME2 NOT NULL DEFAULT GETDATE(),
        changed_by NVARCHAR(256) NULL DEFAULT SUSER_SNAME()
    );
    
    CREATE INDEX IX_audit_log_table_record 
    ON dbo.audit_log(table_name, record_id, changed_at DESC);
    
    PRINT 'Created audit_log table';
END
ELSE
BEGIN
    PRINT 'audit_log table already exists';
END
GO

-- =====================================================================
-- 9. Create stored procedure to reassign user tasks
-- =====================================================================
IF OBJECT_ID('dbo.sp_reassign_user_work', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_reassign_user_work;
GO

CREATE PROCEDURE dbo.sp_reassign_user_work
    @from_user_id INT,
    @to_user_id INT,
    @project_id INT = NULL,
    @include_services BIT = 1,
    @include_reviews BIT = 1
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @services_reassigned INT = 0;
    DECLARE @reviews_reassigned INT = 0;
    
    BEGIN TRANSACTION;
    
    BEGIN TRY
        -- Reassign services
        IF @include_services = 1
        BEGIN
            UPDATE dbo.ProjectServices
            SET assigned_user_id = @to_user_id,
                updated_at = GETDATE()
            WHERE assigned_user_id = @from_user_id
              AND (@project_id IS NULL OR project_id = @project_id);
            
            SET @services_reassigned = @@ROWCOUNT;
        END
        
        -- Reassign reviews
        IF @include_reviews = 1
        BEGIN
            UPDATE dbo.ServiceReviews
            SET assigned_user_id = @to_user_id
            WHERE assigned_user_id = @from_user_id
              AND (@project_id IS NULL OR service_id IN (
                  SELECT service_id FROM dbo.ProjectServices 
                  WHERE project_id = @project_id
              ));
            
            SET @reviews_reassigned = @@ROWCOUNT;
        END
        
        COMMIT TRANSACTION;
        
        -- Return summary
        SELECT 
            @services_reassigned AS services_reassigned,
            @reviews_reassigned AS reviews_reassigned;
            
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO

PRINT 'Created sp_reassign_user_work stored procedure';
GO

-- =====================================================================
-- 10. Verification queries
-- =====================================================================
PRINT '';
PRINT '=== VERIFICATION RESULTS ===';
PRINT '';

-- Check ProjectServices assignments
DECLARE @ServicesWithAssignment INT;
SELECT @ServicesWithAssignment = COUNT(*) 
FROM dbo.ProjectServices 
WHERE assigned_user_id IS NOT NULL;

DECLARE @TotalServices INT;
SELECT @TotalServices = COUNT(*) FROM dbo.ProjectServices;

PRINT CONCAT('ProjectServices: ', @ServicesWithAssignment, ' of ', @TotalServices, ' have assigned users');

-- Check ServiceReviews assignments
DECLARE @ReviewsWithAssignment INT;
SELECT @ReviewsWithAssignment = COUNT(*) 
FROM dbo.ServiceReviews 
WHERE assigned_user_id IS NOT NULL;

DECLARE @TotalReviews INT;
SELECT @TotalReviews = COUNT(*) FROM dbo.ServiceReviews;

PRINT CONCAT('ServiceReviews: ', @ReviewsWithAssignment, ' of ', @TotalReviews, ' have assigned users');

-- User workload summary
PRINT '';
PRINT 'User Workload Summary:';
SELECT 
    user_name,
    assigned_services_count,
    assigned_reviews_count,
    active_reviews_count,
    overdue_reviews_count,
    projects_count
FROM dbo.vw_user_workload
WHERE assigned_services_count > 0 OR assigned_reviews_count > 0
ORDER BY assigned_reviews_count DESC;

PRINT '';
PRINT '=== MIGRATION COMPLETE ===';
GO
