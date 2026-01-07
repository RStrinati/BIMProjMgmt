USE ProjectManagement;
GO

IF OBJECT_ID('dbo.issue_status_map', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.issue_status_map (
        map_id            INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        source_system     NVARCHAR(32)  NOT NULL,
        raw_status        NVARCHAR(100) NOT NULL,
        normalized_status NVARCHAR(50)  NOT NULL,
        is_closed         BIT           NOT NULL DEFAULT 0,
        is_active         BIT           NOT NULL DEFAULT 1,
        priority          INT           NOT NULL DEFAULT 100,
        created_at        DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at        DATETIME2     NULL
    );
END
GO

IF NOT EXISTS (
    SELECT 1 FROM dbo.issue_status_map
    WHERE source_system = 'ACC' AND raw_status = 'open'
)
BEGIN
    INSERT INTO dbo.issue_status_map (source_system, raw_status, normalized_status, is_closed, priority)
    VALUES
        ('ACC', 'open', 'open', 0, 10),
        ('ACC', 'in_progress', 'in_progress', 0, 20),
        ('ACC', 'closed', 'closed', 1, 30),
        ('ACC', 'deleted', 'deleted', 1, 40);
END
GO

IF NOT EXISTS (
    SELECT 1 FROM dbo.issue_status_map
    WHERE source_system = 'Revizto' AND raw_status = 'open'
)
BEGIN
    INSERT INTO dbo.issue_status_map (source_system, raw_status, normalized_status, is_closed, priority)
    VALUES
        ('Revizto', 'open', 'open', 0, 10),
        ('Revizto', 'in_progress', 'in_progress', 0, 20),
        ('Revizto', 'closed', 'closed', 1, 30),
        ('Revizto', 'solved', 'closed', 1, 31),
        ('Revizto', 'resolved', 'closed', 1, 32),
        ('Revizto', 'done', 'closed', 1, 33),
        ('Revizto', 'complete', 'closed', 1, 34),
        ('Revizto', 'completed', 'closed', 1, 35);
END
GO
