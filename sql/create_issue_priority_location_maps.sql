USE ProjectManagement;
GO

IF OBJECT_ID('dbo.issue_priority_map', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.issue_priority_map (
        priority_map_id INT IDENTITY(1,1) PRIMARY KEY,
        source_system NVARCHAR(20) NOT NULL,
        project_id NVARCHAR(100) NULL,
        raw_priority NVARCHAR(100) NOT NULL,
        normalized_priority NVARCHAR(50) NOT NULL,
        is_default BIT NOT NULL DEFAULT 0,
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );

    CREATE UNIQUE INDEX ux_issue_priority_map
        ON dbo.issue_priority_map(source_system, project_id, raw_priority);
END
GO

IF OBJECT_ID('dbo.issue_location_map', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.issue_location_map (
        location_map_id INT IDENTITY(1,1) PRIMARY KEY,
        source_system NVARCHAR(20) NOT NULL,
        project_id NVARCHAR(100) NULL,
        raw_location NVARCHAR(255) NOT NULL,
        location_root NVARCHAR(255) NULL,
        location_building NVARCHAR(255) NULL,
        location_level NVARCHAR(255) NULL,
        is_default BIT NOT NULL DEFAULT 0,
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );

    CREATE UNIQUE INDEX ux_issue_location_map
        ON dbo.issue_location_map(source_system, project_id, raw_location);
END
GO

-- Default priority mapping (global)
IF NOT EXISTS (
    SELECT 1 FROM dbo.issue_priority_map
    WHERE source_system = 'ACC' AND project_id IS NULL AND raw_priority = 'Critical'
)
BEGIN
    INSERT INTO dbo.issue_priority_map (source_system, project_id, raw_priority, normalized_priority, is_default)
    VALUES
        ('ACC', NULL, 'Blocker', 'Critical', 1),
        ('ACC', NULL, 'Critical', 'Critical', 1),
        ('ACC', NULL, 'L1 - Critical', 'Critical', 1),
        ('ACC', NULL, 'Major', 'High', 1),
        ('ACC', NULL, 'L2 - Important', 'High', 1),
        ('ACC', NULL, 'Minor', 'Medium', 1),
        ('ACC', NULL, 'L3 - Significant', 'Medium', 1),
        ('ACC', NULL, 'Trivial', 'Low', 1),
        ('ACC', NULL, 'L4 - Minor', 'Low', 1),
        ('Revizto', NULL, 'Blocker', 'Critical', 1),
        ('Revizto', NULL, 'Critical', 'Critical', 1),
        ('Revizto', NULL, 'Major', 'High', 1),
        ('Revizto', NULL, 'Minor', 'Medium', 1),
        ('Revizto', NULL, 'Trivial', 'Low', 1);
END
GO
