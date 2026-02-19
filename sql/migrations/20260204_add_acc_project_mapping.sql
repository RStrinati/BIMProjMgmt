-- ========================================================================
-- 20260204: Add ACC project mapping + store ACC project GUID on Issues_Current
-- ========================================================================

USE ProjectManagement;
GO

SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO

-- 1) ACC project mapping table (PM project_id -> ACC bim360_project_id)
IF OBJECT_ID('dbo.acc_project_map', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.acc_project_map (
        map_id INT IDENTITY(1,1) NOT NULL,
        pm_project_id INT NOT NULL,
        acc_project_id UNIQUEIDENTIFIER NOT NULL,
        acc_project_name NVARCHAR(510) NULL,
        is_active BIT NOT NULL CONSTRAINT DF_acc_project_map_is_active DEFAULT (1),
        created_at DATETIME2 NOT NULL CONSTRAINT DF_acc_project_map_created_at DEFAULT (SYSUTCDATETIME()),
        updated_at DATETIME2 NULL,
        CONSTRAINT PK_acc_project_map PRIMARY KEY CLUSTERED (map_id),
        CONSTRAINT UQ_acc_project_map_pm UNIQUE (pm_project_id),
        CONSTRAINT UQ_acc_project_map_acc UNIQUE (acc_project_id)
    );
END
GO

-- 2) Store ACC project GUID on Issues_Current (nullable)
IF COL_LENGTH('dbo.Issues_Current', 'acc_project_id') IS NULL
BEGIN
    ALTER TABLE dbo.Issues_Current
        ADD acc_project_id UNIQUEIDENTIFIER NULL;
END
GO

-- 3) Backfill acc_project_id from mapping table (safe/no-op if empty)
UPDATE ic
SET ic.acc_project_id = apm.acc_project_id
FROM dbo.Issues_Current ic
INNER JOIN dbo.acc_project_map apm
    ON apm.pm_project_id = TRY_CAST(ic.source_project_id AS INT)
    AND apm.is_active = 1
WHERE ic.source_system = 'ACC'
  AND ic.acc_project_id IS NULL;
GO

-- 4) Index for display_id lookups
IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_IssuesCurrent_AccProject'
      AND object_id = OBJECT_ID('dbo.Issues_Current')
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_IssuesCurrent_AccProject
        ON dbo.Issues_Current(acc_project_id)
        WHERE acc_project_id IS NOT NULL;
END
GO
