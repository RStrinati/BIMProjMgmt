USE ProjectManagement;
GO

IF OBJECT_ID('dbo.issue_discipline_map', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.issue_discipline_map (
        discipline_map_id     INT           NOT NULL IDENTITY(1,1) PRIMARY KEY,
        source_system         NVARCHAR(32)  NOT NULL,
        raw_discipline        NVARCHAR(255) NOT NULL,
        normalized_discipline NVARCHAR(100) NULL,
        project_id            NVARCHAR(100) NULL,
        is_default            BIT           NOT NULL DEFAULT 0,
        active_flag           BIT           NOT NULL DEFAULT 1,
        created_at            DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at            DATETIME2     NULL
    );

    CREATE INDEX IX_issue_discipline_map_lookup
        ON dbo.issue_discipline_map(source_system, raw_discipline, project_id, active_flag);
END
GO
