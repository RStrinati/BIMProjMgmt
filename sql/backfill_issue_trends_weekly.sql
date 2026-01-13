USE ProjectManagement;
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'mart')
BEGIN
    EXEC('CREATE SCHEMA mart');
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.tables t
    JOIN sys.schemas s ON t.schema_id = s.schema_id
    WHERE s.name = 'mart' AND t.name = 'issue_trends_weekly'
)
BEGIN
    CREATE TABLE mart.issue_trends_weekly (
        week_start date NOT NULL,
        project_sk int NOT NULL,
        client_sk int NOT NULL,
        project_type_sk int NOT NULL,
        open_issues int NOT NULL,
        closed_issues int NOT NULL,
        total_issues int NOT NULL,
        updated_at datetime2(0) NOT NULL
            CONSTRAINT DF_issue_trends_weekly_updated_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_issue_trends_weekly PRIMARY KEY CLUSTERED (
            week_start, project_sk, client_sk, project_type_sk
        )
    );
END
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'ix_issue_trends_weekly_date' AND object_id = OBJECT_ID('mart.issue_trends_weekly')
)
CREATE NONCLUSTERED INDEX ix_issue_trends_weekly_date
    ON mart.issue_trends_weekly (week_start)
    INCLUDE (open_issues, closed_issues, total_issues);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'ix_issue_trends_weekly_project_date' AND object_id = OBJECT_ID('mart.issue_trends_weekly')
)
CREATE NONCLUSTERED INDEX ix_issue_trends_weekly_project_date
    ON mart.issue_trends_weekly (project_sk, week_start)
    INCLUDE (open_issues, closed_issues, total_issues, client_sk, project_type_sk);
GO

DECLARE @start_date date;
SELECT @start_date = MIN(d.[date])
FROM fact.issue_snapshot s
JOIN dim.date d ON s.snapshot_date_sk = d.date_sk;

IF @start_date IS NULL
BEGIN
    PRINT 'No rows found in fact.issue_snapshot. Run warehouse.usp_backfill_issue_snapshot first.';
    RETURN;
END

DELETE FROM mart.issue_trends_weekly;

WITH snapshot_dates AS (
    SELECT
        d.date_sk,
        d.[date],
        d.week_start_date
    FROM dim.date d
),
latest_week_snapshots AS (
    SELECT
        sd.week_start_date,
        MAX(sd.[date]) AS snapshot_date
    FROM fact.issue_snapshot s
    JOIN snapshot_dates sd ON s.snapshot_date_sk = sd.date_sk
    GROUP BY sd.week_start_date
),
latest_week_date_sk AS (
    SELECT
        lw.week_start_date,
        sd.date_sk
    FROM latest_week_snapshots lw
    JOIN snapshot_dates sd ON lw.snapshot_date = sd.[date]
)
INSERT INTO mart.issue_trends_weekly (
    week_start,
    project_sk,
    client_sk,
    project_type_sk,
    open_issues,
    closed_issues,
    total_issues
)
SELECT
    lw.week_start_date AS week_start,
    COALESCE(s.project_sk, 0),
    COALESCE(s.client_sk, 0),
    COALESCE(s.project_type_sk, 0),
    SUM(CASE WHEN s.is_open = 1 THEN 1 ELSE 0 END) AS open_issues,
    SUM(CASE WHEN s.is_closed = 1 THEN 1 ELSE 0 END) AS closed_issues,
    COUNT_BIG(*) AS total_issues
FROM fact.issue_snapshot s
JOIN latest_week_date_sk lw ON s.snapshot_date_sk = lw.date_sk
GROUP BY
    lw.week_start_date,
    COALESCE(s.project_sk, 0),
    COALESCE(s.client_sk, 0),
    COALESCE(s.project_type_sk, 0);
GO

PRINT 'Weekly issue trends backfill complete.';
GO
