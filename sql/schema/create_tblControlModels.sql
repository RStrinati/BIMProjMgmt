-- ============================================================================
-- Control Models Table Bootstrap Script
-- Ensures ProjectManagement.dbo.tblControlModels exists with required columns
-- and supporting indexes for the Revit health control-model workflow.
-- ============================================================================

IF DB_ID(N'ProjectManagement') IS NULL
BEGIN
    RAISERROR('ProjectManagement database not found.', 16, 1);
    RETURN;
END;

USE ProjectManagement;
GO

IF NOT EXISTS (
    SELECT 1
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'dbo'
      AND TABLE_NAME = 'tblControlModels'
)
BEGIN
    PRINT 'Creating dbo.tblControlModels...';
    CREATE TABLE dbo.tblControlModels (
        id                INT IDENTITY(1,1) PRIMARY KEY,
        project_id        INT NOT NULL,
        control_file_name NVARCHAR(510) NOT NULL,
        is_active         BIT NOT NULL CONSTRAINT DF_tblControlModels_is_active DEFAULT (1),
        metadata_json     NVARCHAR(MAX) NULL,
        created_at        DATETIME2(0) NOT NULL CONSTRAINT DF_tblControlModels_created_at DEFAULT (SYSDATETIME()),
        updated_at        DATETIME2(0) NOT NULL CONSTRAINT DF_tblControlModels_updated_at DEFAULT (SYSDATETIME())
    );
END;
GO

-- Ensure required columns exist (for environments where an older version of the table was created)
IF COL_LENGTH('dbo.tblControlModels', 'metadata_json') IS NULL
BEGIN
    PRINT 'Adding metadata_json column to dbo.tblControlModels...';
    ALTER TABLE dbo.tblControlModels
    ADD metadata_json NVARCHAR(MAX) NULL;
END;

IF COL_LENGTH('dbo.tblControlModels', 'created_at') IS NULL
BEGIN
    PRINT 'Adding created_at column to dbo.tblControlModels...';
    ALTER TABLE dbo.tblControlModels
    ADD created_at DATETIME2(0) NOT NULL CONSTRAINT DF_tblControlModels_created_at DEFAULT (SYSDATETIME());
END;

IF COL_LENGTH('dbo.tblControlModels', 'updated_at') IS NULL
BEGIN
    PRINT 'Adding updated_at column to dbo.tblControlModels...';
    ALTER TABLE dbo.tblControlModels
    ADD updated_at DATETIME2(0) NOT NULL CONSTRAINT DF_tblControlModels_updated_at DEFAULT (SYSDATETIME());
END;

-- Normalise constraints in case the table pre-existed without defaults
IF NOT EXISTS (
    SELECT 1
    FROM sys.default_constraints dc
    INNER JOIN sys.columns c
        ON dc.parent_object_id = c.object_id
       AND dc.parent_column_id = c.column_id
    WHERE dc.parent_object_id = OBJECT_ID('dbo.tblControlModels')
      AND c.name = 'is_active'
)
BEGIN
    ALTER TABLE dbo.tblControlModels
    ADD CONSTRAINT DF_tblControlModels_is_active DEFAULT (1) FOR is_active;
END;

IF NOT EXISTS (
    SELECT 1
    FROM sys.default_constraints dc
    INNER JOIN sys.columns c
        ON dc.parent_object_id = c.object_id
       AND dc.parent_column_id = c.column_id
    WHERE dc.parent_object_id = OBJECT_ID('dbo.tblControlModels')
      AND c.name = 'created_at'
)
BEGIN
    ALTER TABLE dbo.tblControlModels
    ADD CONSTRAINT DF_tblControlModels_created_at DEFAULT (SYSDATETIME()) FOR created_at;
END;

IF NOT EXISTS (
    SELECT 1
    FROM sys.default_constraints dc
    INNER JOIN sys.columns c
        ON dc.parent_object_id = c.object_id
       AND dc.parent_column_id = c.column_id
    WHERE dc.parent_object_id = OBJECT_ID('dbo.tblControlModels')
      AND c.name = 'updated_at'
)
BEGIN
    ALTER TABLE dbo.tblControlModels
    ADD CONSTRAINT DF_tblControlModels_updated_at DEFAULT (SYSDATETIME()) FOR updated_at;
END;

-- Helpful index for lookups by project/active status
IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_tblControlModels_ProjectActive'
      AND object_id = OBJECT_ID('dbo.tblControlModels')
)
BEGIN
    CREATE INDEX IX_tblControlModels_ProjectActive
        ON dbo.tblControlModels(project_id, is_active, control_file_name);
END;

PRINT 'tblControlModels bootstrap complete.';
GO
