-- Migration: Add ACCImportGeneralLogs table for project-agnostic imports
-- Date: 2026-02-20

IF NOT EXISTS (
    SELECT 1
    FROM sys.tables
    WHERE name = 'ACCImportGeneralLogs'
      AND SCHEMA_NAME(schema_id) = 'dbo'
)
BEGIN
    CREATE TABLE dbo.ACCImportGeneralLogs (
        log_id INT IDENTITY(1,1) PRIMARY KEY,
        source NVARCHAR(100) NULL,
        folder_name NVARCHAR(1000) NOT NULL,
        import_date DATETIME NOT NULL DEFAULT GETDATE(),
        status NVARCHAR(32) NULL,
        summary NVARCHAR(MAX) NULL,
        execution_time_seconds DECIMAL(10,2) NULL
    );

    CREATE NONCLUSTERED INDEX IX_ACCImportGeneralLogs_ImportDate
        ON dbo.ACCImportGeneralLogs(import_date DESC);

    PRINT 'Created table: dbo.ACCImportGeneralLogs';
END
ELSE
BEGIN
    PRINT 'Table dbo.ACCImportGeneralLogs already exists';
END
GO
