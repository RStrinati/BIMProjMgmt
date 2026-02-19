-- Migration: Add description column to projects
-- Date: 2026-02-02

IF NOT EXISTS (
    SELECT 1
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'projects'
      AND COLUMN_NAME = 'description'
)
BEGIN
    ALTER TABLE dbo.projects
        ADD description NVARCHAR(MAX) NULL;
    PRINT 'Added description column to dbo.projects';
END
ELSE
BEGIN
    PRINT 'Column description already exists on dbo.projects';
END
GO
