USE ProjectManagement;
GO

IF OBJECT_ID('dbo.Issues_Current', 'U') IS NOT NULL
BEGIN
    IF EXISTS (
        SELECT 1
        FROM sys.key_constraints
        WHERE name = 'pk_issues_current'
          AND parent_object_id = OBJECT_ID('dbo.Issues_Current')
    )
    BEGIN
        ALTER TABLE dbo.Issues_Current DROP CONSTRAINT pk_issues_current;
    END

    IF NOT EXISTS (
        SELECT 1
        FROM sys.key_constraints
        WHERE name = 'pk_issues_current_source'
          AND parent_object_id = OBJECT_ID('dbo.Issues_Current')
    )
    BEGIN
        ALTER TABLE dbo.Issues_Current
            ADD CONSTRAINT pk_issues_current_source
            PRIMARY KEY CLUSTERED (source_system, source_project_id, source_issue_id);
    END
END
GO

IF OBJECT_ID('dbo.Issues_Snapshots', 'U') IS NOT NULL
BEGIN
    IF EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE name = 'uq_issues_snapshots_key_date'
          AND object_id = OBJECT_ID('dbo.Issues_Snapshots')
    )
    BEGIN
        DROP INDEX uq_issues_snapshots_key_date ON dbo.Issues_Snapshots;
    END

    IF NOT EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE name = 'uq_issues_snapshots_source_date'
          AND object_id = OBJECT_ID('dbo.Issues_Snapshots')
    )
    BEGIN
        CREATE UNIQUE INDEX uq_issues_snapshots_source_date
            ON dbo.Issues_Snapshots (
                source_system,
                source_project_id,
                source_issue_id,
                snapshot_date,
                import_run_id
            );
    END
END
GO
