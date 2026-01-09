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
    WHERE s.name = 'mart' AND t.name = 'issue_trends_daily'
)
BEGIN
    CREATE TABLE mart.issue_trends_daily (
        snapshot_date date NOT NULL,
        project_sk int NOT NULL,
        client_sk int NOT NULL,
        project_type_sk int NOT NULL,
        open_issues int NOT NULL,
        closed_issues int NOT NULL,
        backlog_age_total float NULL,
        backlog_age_count int NULL,
        resolution_total float NULL,
        resolution_count int NULL,
        urgency_total float NULL,
        urgency_count int NULL,
        sentiment_total float NULL,
        sentiment_count int NULL,
        updated_at datetime2(0) NOT NULL
            CONSTRAINT DF_issue_trends_daily_updated_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_issue_trends_daily PRIMARY KEY CLUSTERED (
            snapshot_date, project_sk, client_sk, project_type_sk
        )
    );
END
GO

IF EXISTS (
    SELECT 1
    FROM sys.tables t
    JOIN sys.schemas s ON t.schema_id = s.schema_id
    WHERE s.name = 'mart' AND t.name = 'issue_trends_daily'
)
BEGIN
    ALTER TABLE mart.issue_trends_daily ALTER COLUMN project_sk int NOT NULL;
    ALTER TABLE mart.issue_trends_daily ALTER COLUMN client_sk int NOT NULL;
    ALTER TABLE mart.issue_trends_daily ALTER COLUMN project_type_sk int NOT NULL;

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE name = 'PK_issue_trends_daily' AND object_id = OBJECT_ID('mart.issue_trends_daily')
    )
    BEGIN
        ALTER TABLE mart.issue_trends_daily
        ADD CONSTRAINT PK_issue_trends_daily PRIMARY KEY CLUSTERED (
            snapshot_date, project_sk, client_sk, project_type_sk
        );
    END
END
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'ix_issue_trends_daily_date' AND object_id = OBJECT_ID('mart.issue_trends_daily')
)
CREATE NONCLUSTERED INDEX ix_issue_trends_daily_date
    ON mart.issue_trends_daily (snapshot_date)
    INCLUDE (open_issues, closed_issues, backlog_age_total, backlog_age_count,
             resolution_total, resolution_count, urgency_total, urgency_count,
             sentiment_total, sentiment_count);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'ix_issue_trends_daily_project_date' AND object_id = OBJECT_ID('mart.issue_trends_daily')
)
CREATE NONCLUSTERED INDEX ix_issue_trends_daily_project_date
    ON mart.issue_trends_daily (project_sk, snapshot_date)
    INCLUDE (open_issues, closed_issues, backlog_age_total, backlog_age_count,
             resolution_total, resolution_count, urgency_total, urgency_count,
             sentiment_total, sentiment_count, client_sk, project_type_sk);
GO

CREATE OR ALTER PROCEDURE mart.usp_refresh_issue_trends_daily
    @days_back int = 60
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @start_date date = DATEADD(day, -@days_back, CAST(GETDATE() AS date));

    DELETE FROM mart.issue_trends_daily
    WHERE snapshot_date >= @start_date;

    INSERT INTO mart.issue_trends_daily (
        snapshot_date,
        project_sk,
        client_sk,
        project_type_sk,
        open_issues,
        closed_issues,
        backlog_age_total,
        backlog_age_count,
        resolution_total,
        resolution_count,
        urgency_total,
        urgency_count,
        sentiment_total,
        sentiment_count
    )
    SELECT
        CAST(d.[date] AS date) AS snapshot_date,
        COALESCE(s.project_sk, 0),
        COALESCE(s.client_sk, 0),
        COALESCE(s.project_type_sk, 0),
        SUM(CASE WHEN s.is_open = 1 THEN 1 ELSE 0 END) AS open_issues,
        SUM(CASE WHEN s.is_closed = 1 THEN 1 ELSE 0 END) AS closed_issues,
        SUM(CASE WHEN s.backlog_age_days IS NOT NULL AND s.backlog_age_days <> 0 THEN s.backlog_age_days ELSE 0 END) AS backlog_age_total,
        SUM(CASE WHEN s.backlog_age_days IS NOT NULL AND s.backlog_age_days <> 0 THEN 1 ELSE 0 END) AS backlog_age_count,
        SUM(CASE WHEN s.resolution_days IS NOT NULL AND s.resolution_days <> 0 THEN s.resolution_days ELSE 0 END) AS resolution_total,
        SUM(CASE WHEN s.resolution_days IS NOT NULL AND s.resolution_days <> 0 THEN 1 ELSE 0 END) AS resolution_count,
        SUM(CASE WHEN s.urgency_score IS NOT NULL AND s.urgency_score <> 0 THEN s.urgency_score ELSE 0 END) AS urgency_total,
        SUM(CASE WHEN s.urgency_score IS NOT NULL AND s.urgency_score <> 0 THEN 1 ELSE 0 END) AS urgency_count,
        SUM(CASE WHEN s.sentiment_score IS NOT NULL AND s.sentiment_score <> 0 THEN s.sentiment_score ELSE 0 END) AS sentiment_total,
        SUM(CASE WHEN s.sentiment_score IS NOT NULL AND s.sentiment_score <> 0 THEN 1 ELSE 0 END) AS sentiment_count
    FROM fact.issue_snapshot s
    JOIN dim.date d ON s.snapshot_date_sk = d.date_sk
    WHERE d.[date] >= @start_date
    GROUP BY
        CAST(d.[date] AS date),
        COALESCE(s.project_sk, 0),
        COALESCE(s.client_sk, 0),
        COALESCE(s.project_type_sk, 0);
END
GO
