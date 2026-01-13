USE ProjectManagement;
GO

SET QUOTED_IDENTIFIER ON;
SET ANSI_NULLS ON;
SET ANSI_WARNINGS ON;
GO

MERGE dbo.issue_status_map AS target
USING (
    SELECT
        'ACC' AS source_system,
        v.raw_status,
        v.normalized_status,
        v.is_closed,
        1 AS is_active,
        100 AS priority
    FROM (VALUES
        ('completed', 'closed', 1),
        ('in_review', 'in_progress', 0),
        ('pending', 'open', 0),
        ('draft', 'open', 0),
        ('in_dispute', 'in_progress', 0)
    ) AS v(raw_status, normalized_status, is_closed)
) AS src
ON target.source_system = src.source_system
AND target.raw_status = src.raw_status
WHEN NOT MATCHED THEN
    INSERT (
        source_system,
        raw_status,
        normalized_status,
        is_closed,
        is_active,
        priority,
        created_at,
        updated_at
    )
    VALUES (
        src.source_system,
        src.raw_status,
        src.normalized_status,
        src.is_closed,
        src.is_active,
        src.priority,
        SYSUTCDATETIME(),
        NULL
    )
WHEN MATCHED THEN
    UPDATE SET
        normalized_status = src.normalized_status,
        is_closed = src.is_closed,
        is_active = src.is_active,
        priority = src.priority,
        updated_at = SYSUTCDATETIME();
GO
