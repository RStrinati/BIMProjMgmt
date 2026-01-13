USE ProjectManagement;
GO

IF OBJECT_ID('dbo.Issues_Current', 'U') IS NOT NULL
BEGIN
    IF COL_LENGTH('dbo.Issues_Current', 'issue_key_hash') IS NOT NULL
    BEGIN
        ALTER TABLE dbo.Issues_Current DROP COLUMN issue_key_hash;
    END

    ALTER TABLE dbo.Issues_Current
        ADD issue_key_hash VARBINARY(32) NULL;
END
GO

IF OBJECT_ID('dbo.Issues_Current', 'U') IS NOT NULL
BEGIN
    UPDATE dbo.Issues_Current
    SET issue_key_hash = HASHBYTES(
        'SHA2_256',
        CONCAT(source_system, '|', source_project_id, '|', source_issue_id)
    );
END
GO

IF OBJECT_ID('dbo.Issues_Current', 'U') IS NOT NULL
BEGIN
    ALTER TABLE dbo.Issues_Current
        ALTER COLUMN issue_key_hash VARBINARY(32) NOT NULL;

    IF EXISTS (
        SELECT 1
        FROM sys.key_constraints
        WHERE name IN ('pk_issues_current', 'pk_issues_current_source', 'pk_issues_current_hash')
          AND parent_object_id = OBJECT_ID('dbo.Issues_Current')
    )
    BEGIN
        DECLARE @pk_name SYSNAME;
        SELECT TOP 1 @pk_name = name
        FROM sys.key_constraints
        WHERE name IN ('pk_issues_current', 'pk_issues_current_source', 'pk_issues_current_hash')
          AND parent_object_id = OBJECT_ID('dbo.Issues_Current');
        EXEC('ALTER TABLE dbo.Issues_Current DROP CONSTRAINT ' + @pk_name);
    END

    IF NOT EXISTS (
        SELECT 1
        FROM sys.key_constraints
        WHERE name = 'pk_issues_current_hash'
          AND parent_object_id = OBJECT_ID('dbo.Issues_Current')
    )
    BEGIN
        ALTER TABLE dbo.Issues_Current
            ADD CONSTRAINT pk_issues_current_hash
            PRIMARY KEY CLUSTERED (issue_key_hash);
    END
END
GO

IF OBJECT_ID('dbo.Issues_Snapshots', 'U') IS NOT NULL
BEGIN
    IF EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE name IN ('uq_issues_snapshots_key_date', 'uq_issues_snapshots_source_date', 'uq_issues_snapshots_hash_date')
          AND object_id = OBJECT_ID('dbo.Issues_Snapshots')
    )
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
        IF EXISTS (
            SELECT 1
            FROM sys.indexes
            WHERE name = 'uq_issues_snapshots_source_date'
              AND object_id = OBJECT_ID('dbo.Issues_Snapshots')
        )
        BEGIN
            DROP INDEX uq_issues_snapshots_source_date ON dbo.Issues_Snapshots;
        END
        IF EXISTS (
            SELECT 1
            FROM sys.indexes
            WHERE name = 'uq_issues_snapshots_hash_date'
              AND object_id = OBJECT_ID('dbo.Issues_Snapshots')
        )
        BEGIN
            DROP INDEX uq_issues_snapshots_hash_date ON dbo.Issues_Snapshots;
        END
    END

    IF COL_LENGTH('dbo.Issues_Snapshots', 'issue_key_hash') IS NOT NULL
    BEGIN
        ALTER TABLE dbo.Issues_Snapshots DROP COLUMN issue_key_hash;
    END

    ALTER TABLE dbo.Issues_Snapshots
        ADD issue_key_hash VARBINARY(32) NULL;
END
GO

IF OBJECT_ID('dbo.Issues_Snapshots', 'U') IS NOT NULL
BEGIN
    UPDATE dbo.Issues_Snapshots
    SET issue_key_hash = HASHBYTES(
        'SHA2_256',
        CONCAT(source_system, '|', source_project_id, '|', source_issue_id)
    );
END
GO

IF OBJECT_ID('dbo.Issues_Snapshots', 'U') IS NOT NULL
BEGIN
    ALTER TABLE dbo.Issues_Snapshots
        ALTER COLUMN issue_key_hash VARBINARY(32) NOT NULL;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE name = 'uq_issues_snapshots_hash_date'
          AND object_id = OBJECT_ID('dbo.Issues_Snapshots')
    )
    BEGIN
        CREATE UNIQUE INDEX uq_issues_snapshots_hash_date
            ON dbo.Issues_Snapshots (issue_key_hash, snapshot_date, import_run_id);
    END
END
GO
