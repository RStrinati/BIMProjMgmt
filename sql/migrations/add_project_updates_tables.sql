-- Project Updates Feature
-- Migration: Add project_updates and project_update_comments tables
-- Date: 2026-01-18

-- =====================================================
-- Table: project_updates
-- Purpose: Store project status updates/activity feed
-- =====================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'project_updates' AND SCHEMA_NAME(schema_id) = 'dbo')
BEGIN
    CREATE TABLE dbo.project_updates (
        update_id INT IDENTITY(1,1) PRIMARY KEY,
        project_id INT NOT NULL,
        body NVARCHAR(MAX) NOT NULL,
        created_by INT NULL,  -- FK to Users.user_id
        created_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        updated_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        is_deleted BIT NOT NULL DEFAULT 0,
        
        CONSTRAINT FK_project_updates_project
            FOREIGN KEY (project_id) REFERENCES dbo.Projects(project_id)
            ON DELETE CASCADE,
        
        CONSTRAINT FK_project_updates_user
            FOREIGN KEY (created_by) REFERENCES dbo.Users(user_id)
            ON DELETE SET NULL
    );
    
    CREATE NONCLUSTERED INDEX IX_project_updates_project_id
        ON dbo.project_updates(project_id, created_at DESC);
    
    CREATE NONCLUSTERED INDEX IX_project_updates_created_at
        ON dbo.project_updates(created_at DESC);
    
    PRINT 'Created table: dbo.project_updates';
END
ELSE
BEGIN
    PRINT 'Table dbo.project_updates already exists';
END
GO

-- =====================================================
-- Table: project_update_comments
-- Purpose: Store comments on project updates
-- =====================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'project_update_comments' AND SCHEMA_NAME(schema_id) = 'dbo')
BEGIN
    CREATE TABLE dbo.project_update_comments (
        comment_id INT IDENTITY(1,1) PRIMARY KEY,
        update_id INT NOT NULL,
        body NVARCHAR(MAX) NOT NULL,
        created_by INT NULL,  -- FK to Users.user_id
        created_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        updated_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        is_deleted BIT NOT NULL DEFAULT 0,
        
        CONSTRAINT FK_project_update_comments_update
            FOREIGN KEY (update_id) REFERENCES dbo.project_updates(update_id)
            ON DELETE CASCADE,
        
        CONSTRAINT FK_project_update_comments_user
            FOREIGN KEY (created_by) REFERENCES dbo.Users(user_id)
            ON DELETE SET NULL
    );
    
    CREATE NONCLUSTERED INDEX IX_project_update_comments_update_id
        ON dbo.project_update_comments(update_id, created_at ASC);
    
    PRINT 'Created table: dbo.project_update_comments';
END
ELSE
BEGIN
    PRINT 'Table dbo.project_update_comments already exists';
END
GO

PRINT 'Project updates migration complete';
