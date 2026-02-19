USE ProjectManagement;
GO

PRINT 'Adding performance indexes for Issues_Current...';
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_IssuesCurrent_UpdatedAt'
      AND object_id = OBJECT_ID('dbo.Issues_Current')
)
BEGIN
    PRINT 'Creating index: IX_IssuesCurrent_UpdatedAt';
    CREATE NONCLUSTERED INDEX IX_IssuesCurrent_UpdatedAt
        ON dbo.Issues_Current(updated_at)
        INCLUDE (
            issue_key,
            source_system,
            source_issue_id,
            source_project_id,
            project_id,
            status_normalized,
            priority_normalized,
            discipline_normalized,
            assignee_user_key,
            created_at,
            closed_at,
            location_root,
            location_building,
            location_level,
            is_deleted,
            import_run_id
        );
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_IssuesCurrent_SourceUpdated'
      AND object_id = OBJECT_ID('dbo.Issues_Current')
)
BEGIN
    PRINT 'Creating index: IX_IssuesCurrent_SourceUpdated';
    CREATE NONCLUSTERED INDEX IX_IssuesCurrent_SourceUpdated
        ON dbo.Issues_Current(source_system, updated_at)
        INCLUDE (
            issue_key,
            source_issue_id,
            source_project_id,
            project_id,
            status_normalized,
            priority_normalized,
            discipline_normalized,
            assignee_user_key,
            created_at,
            closed_at,
            location_root,
            location_building,
            location_level,
            is_deleted,
            import_run_id
        );
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_IssuesCurrent_ProjectUpdated'
      AND object_id = OBJECT_ID('dbo.Issues_Current')
)
BEGIN
    PRINT 'Creating index: IX_IssuesCurrent_ProjectUpdated';
    CREATE NONCLUSTERED INDEX IX_IssuesCurrent_ProjectUpdated
        ON dbo.Issues_Current(project_id, updated_at)
        INCLUDE (
            issue_key,
            source_system,
            source_issue_id,
            source_project_id,
            status_normalized,
            priority_normalized,
            discipline_normalized,
            assignee_user_key,
            created_at,
            closed_at,
            location_root,
            location_building,
            location_level,
            is_deleted,
            import_run_id
        );
END
GO

PRINT 'Updating Issues_Current statistics...';
UPDATE STATISTICS dbo.Issues_Current WITH FULLSCAN;
GO
