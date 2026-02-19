USE ProjectManagement;
GO

IF OBJECT_ID('dbo.issue_discipline_map', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.issue_discipline_map (
        discipline_map_id INT IDENTITY(1,1) PRIMARY KEY,
        source_system NVARCHAR(20) NOT NULL,
        project_id NVARCHAR(100) NULL,
        raw_discipline NVARCHAR(255) NOT NULL,
        normalized_discipline NVARCHAR(255) NOT NULL,
        is_default BIT NOT NULL DEFAULT 0,
        is_active BIT NOT NULL DEFAULT 1,
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );

    CREATE UNIQUE INDEX ux_issue_discipline_map
        ON dbo.issue_discipline_map(source_system, project_id, raw_discipline);
END
GO
