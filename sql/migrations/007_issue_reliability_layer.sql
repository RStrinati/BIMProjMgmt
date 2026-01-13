USE ProjectManagement;
GO

IF OBJECT_ID('dbo.IssueImportRuns', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.IssueImportRuns (
        import_run_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        source_system NVARCHAR(50) NOT NULL,
        run_type NVARCHAR(50) NOT NULL,
        started_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        completed_at DATETIME2 NULL,
        status NVARCHAR(20) NOT NULL,
        source_watermark DATETIME2 NULL,
        row_count INT NULL,
        notes NVARCHAR(1000) NULL
    );
    CREATE INDEX ix_issueimportruns_status ON dbo.IssueImportRuns(status, started_at);
END
GO

IF OBJECT_ID('dbo.IssueDataQualityResults', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.IssueDataQualityResults (
        result_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        import_run_id INT NOT NULL,
        check_name NVARCHAR(200) NOT NULL,
        severity NVARCHAR(20) NOT NULL,
        passed BIT NOT NULL,
        details NVARCHAR(2000) NULL,
        checked_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT fk_issuequality_run
            FOREIGN KEY (import_run_id) REFERENCES dbo.IssueImportRuns(import_run_id)
    );
    CREATE INDEX ix_issuequality_run ON dbo.IssueDataQualityResults(import_run_id, passed);
END
GO

IF OBJECT_ID('dbo.Issues_Current', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Issues_Current (
        issue_key NVARCHAR(512) NOT NULL,
        source_system NVARCHAR(50) NOT NULL,
        source_issue_id NVARCHAR(255) NOT NULL,
        source_project_id NVARCHAR(255) NOT NULL,
        project_id NVARCHAR(100) NULL,
        status_raw NVARCHAR(100) NULL,
        status_normalized NVARCHAR(50) NULL,
        priority_raw NVARCHAR(100) NULL,
        priority_normalized NVARCHAR(50) NULL,
        discipline_raw NVARCHAR(100) NULL,
        discipline_normalized NVARCHAR(100) NULL,
        assignee_user_key NVARCHAR(255) NULL,
        created_at DATETIME2 NULL,
        updated_at DATETIME2 NULL,
        closed_at DATETIME2 NULL,
        location_root NVARCHAR(255) NULL,
        location_building NVARCHAR(255) NULL,
        location_level NVARCHAR(255) NULL,
        is_deleted BIT NULL,
        project_mapped BIT NULL,
        import_run_id INT NOT NULL,
        snapshot_id INT NULL,
        load_ts DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT pk_issues_current PRIMARY KEY (issue_key),
        CONSTRAINT fk_issues_current_run
            FOREIGN KEY (import_run_id) REFERENCES dbo.IssueImportRuns(import_run_id)
    );
    CREATE INDEX ix_issues_current_project ON dbo.Issues_Current(project_id, status_normalized);
END
GO

IF OBJECT_ID('dbo.Issues_Snapshots', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Issues_Snapshots (
        snapshot_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        snapshot_date DATE NOT NULL,
        import_run_id INT NOT NULL,
        issue_key NVARCHAR(512) NOT NULL,
        source_system NVARCHAR(50) NOT NULL,
        source_issue_id NVARCHAR(255) NOT NULL,
        source_project_id NVARCHAR(255) NOT NULL,
        project_id NVARCHAR(100) NULL,
        status_normalized NVARCHAR(50) NULL,
        priority_normalized NVARCHAR(50) NULL,
        discipline_normalized NVARCHAR(100) NULL,
        location_root NVARCHAR(255) NULL,
        is_open BIT NOT NULL,
        is_closed BIT NOT NULL,
        backlog_age_days INT NULL,
        resolution_days INT NULL,
        created_at DATETIME2 NULL,
        updated_at DATETIME2 NULL,
        closed_at DATETIME2 NULL,
        load_ts DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT fk_issues_snapshots_run
            FOREIGN KEY (import_run_id) REFERENCES dbo.IssueImportRuns(import_run_id)
    );
    CREATE UNIQUE INDEX uq_issues_snapshots_key_date
        ON dbo.Issues_Snapshots(issue_key, snapshot_date, import_run_id);
    CREATE INDEX ix_issues_snapshots_date
        ON dbo.Issues_Snapshots(snapshot_date, project_id);
END
GO
