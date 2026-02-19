-- ========================================================================
-- 20260205: Add acc_project_id to project_aliases
-- ========================================================================

USE ProjectManagement;
GO

SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO

IF COL_LENGTH('dbo.project_aliases', 'acc_project_id') IS NULL
BEGIN
    ALTER TABLE dbo.project_aliases
        ADD acc_project_id UNIQUEIDENTIFIER NULL;
END
GO

-- Backfill from acc_project_map where available (one per pm_project_id)
UPDATE pa
SET pa.acc_project_id = apm.acc_project_id
FROM dbo.project_aliases pa
INNER JOIN dbo.acc_project_map apm
    ON apm.pm_project_id = pa.pm_project_id
    AND apm.is_active = 1
WHERE pa.acc_project_id IS NULL;
GO

-- Index for lookups
IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_project_aliases_acc_project_id'
      AND object_id = OBJECT_ID('dbo.project_aliases')
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_project_aliases_acc_project_id
        ON dbo.project_aliases(acc_project_id)
        WHERE acc_project_id IS NOT NULL;
END
GO

