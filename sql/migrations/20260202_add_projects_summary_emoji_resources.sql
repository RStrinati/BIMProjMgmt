-- Migration: Add summary + emoji to projects and create project_resources
-- Date: 2026-02-02

IF NOT EXISTS (
    SELECT 1
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'projects'
      AND COLUMN_NAME = 'summary'
)
BEGIN
    ALTER TABLE dbo.projects
        ADD summary NVARCHAR(500) NULL;
    PRINT 'Added summary column to dbo.projects';
END
ELSE
BEGIN
    PRINT 'Column summary already exists on dbo.projects';
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'projects'
      AND COLUMN_NAME = 'emoji'
)
BEGIN
    ALTER TABLE dbo.projects
        ADD emoji NVARCHAR(16) NULL;
    PRINT 'Added emoji column to dbo.projects';
END
ELSE
BEGIN
    PRINT 'Column emoji already exists on dbo.projects';
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'projects'
      AND COLUMN_NAME = 'icon_key'
)
BEGIN
    ALTER TABLE dbo.projects
        ADD icon_key NVARCHAR(64) NULL;
    PRINT 'Added icon_key column to dbo.projects';
END
ELSE
BEGIN
    PRINT 'Column icon_key already exists on dbo.projects';
END
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'project_resources' AND SCHEMA_NAME(schema_id) = 'dbo')
BEGIN
    CREATE TABLE dbo.project_resources (
        resource_id INT IDENTITY(1,1) PRIMARY KEY,
        project_id INT NOT NULL,
        title NVARCHAR(255) NOT NULL,
        url NVARCHAR(2048) NOT NULL,
        created_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        updated_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        is_deleted BIT NOT NULL DEFAULT 0,

        CONSTRAINT FK_project_resources_project
            FOREIGN KEY (project_id) REFERENCES dbo.projects(project_id)
            ON DELETE CASCADE
    );

    CREATE NONCLUSTERED INDEX IX_project_resources_project_id
        ON dbo.project_resources(project_id, created_at DESC);

    PRINT 'Created table: dbo.project_resources';
END
ELSE
BEGIN
    PRINT 'Table dbo.project_resources already exists';
END
GO
