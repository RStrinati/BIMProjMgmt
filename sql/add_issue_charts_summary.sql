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
    WHERE s.name = 'mart' AND t.name = 'issue_charts_daily'
)
BEGIN
    CREATE TABLE mart.issue_charts_daily (
        snapshot_date date NOT NULL,
        project_bk int NOT NULL,
        client_bk int NOT NULL,
        project_type_bk int NOT NULL,
        status_group nvarchar(40) NOT NULL,
        priority_group nvarchar(50) NOT NULL,
        discipline_group nvarchar(100) NOT NULL,
        zone_root nvarchar(100) NOT NULL,
        open_issues int NOT NULL,
        closed_issues int NOT NULL,
        total_issues int NOT NULL,
        updated_at datetime2(0) NOT NULL
            CONSTRAINT DF_issue_charts_daily_updated_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_issue_charts_daily PRIMARY KEY CLUSTERED (
            snapshot_date,
            project_bk,
            client_bk,
            project_type_bk,
            status_group,
            priority_group,
            discipline_group,
            zone_root
        )
    );
END
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'ix_issue_charts_daily_date' AND object_id = OBJECT_ID('mart.issue_charts_daily')
)
CREATE NONCLUSTERED INDEX ix_issue_charts_daily_date
    ON mart.issue_charts_daily (snapshot_date)
    INCLUDE (status_group, priority_group, discipline_group, zone_root,
             open_issues, closed_issues, total_issues,
             project_bk, client_bk, project_type_bk);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'ix_issue_charts_daily_project_date' AND object_id = OBJECT_ID('mart.issue_charts_daily')
)
CREATE NONCLUSTERED INDEX ix_issue_charts_daily_project_date
    ON mart.issue_charts_daily (project_bk, snapshot_date)
    INCLUDE (status_group, priority_group, discipline_group, zone_root,
             open_issues, closed_issues, total_issues,
             client_bk, project_type_bk);
GO

CREATE OR ALTER PROCEDURE mart.usp_refresh_issue_charts_daily
    @days_back int = 90,
    @start_date date = NULL,
    @end_date date = NULL
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @min_snapshot_date date;
    DECLARE @max_snapshot_date date;
    SELECT
        @min_snapshot_date = MIN(d.[date]),
        @max_snapshot_date = MAX(d.[date])
    FROM fact.issue_snapshot s
    JOIN dim.date d ON s.snapshot_date_sk = d.date_sk;

    IF @max_snapshot_date IS NULL
        RETURN;

    IF @end_date IS NULL
        SET @end_date = @max_snapshot_date;

    IF @start_date IS NULL
        SET @start_date = DATEADD(day, -@days_back, @end_date);

    IF @start_date < @min_snapshot_date
        SET @start_date = @min_snapshot_date;

    DELETE FROM mart.issue_charts_daily
    WHERE snapshot_date >= @start_date AND snapshot_date <= @end_date;

    WITH discipline_pick AS (
        SELECT bic.issue_sk, MAX(ic.level1_name) AS discipline
        FROM brg.issue_category bic
        JOIN dim.issue_category ic
            ON bic.issue_category_sk = ic.issue_category_sk
        WHERE bic.category_role = 'discipline'
        GROUP BY bic.issue_sk
    ),
    acc_issues AS (
        SELECT
            ve.display_id,
            ve.pm_project_id,
            ROW_NUMBER() OVER (
                PARTITION BY ve.display_id
                ORDER BY ve.created_at DESC, ve.issue_id DESC
            ) AS rn
        FROM acc_data_schema.dbo.vw_issues_expanded ve
    )
    INSERT INTO mart.issue_charts_daily (
        snapshot_date,
        project_bk,
        client_bk,
        project_type_bk,
        status_group,
        priority_group,
        discipline_group,
        zone_root,
        open_issues,
        closed_issues,
        total_issues
    )
    SELECT
        CAST(d.[date] AS date) AS snapshot_date,
        COALESCE(p.project_bk, ve.pm_project_id, 0) AS project_bk,
        COALESCE(p.client_sk, 0) AS client_bk,
        COALESCE(p.project_type_sk, 0) AS project_type_bk,
        CASE
            WHEN LOWER(ISNULL(COALESCE(s.status, i.status), '')) LIKE '%open%' THEN 'Open'
            WHEN LOWER(ISNULL(COALESCE(s.status, i.status), '')) LIKE '%progress%' THEN 'In progress'
            WHEN LOWER(ISNULL(COALESCE(s.status, i.status), '')) LIKE '%complete%' THEN 'Completed'
            WHEN LOWER(ISNULL(COALESCE(s.status, i.status), '')) LIKE '%close%' THEN 'Closed'
            ELSE 'Other'
        END AS status_group,
        COALESCE(i.priority_normalized, 'Unassigned') AS priority_group,
        COALESCE(
            dp.discipline,
            CASE WHEN i.source_system = 'Revizto' THEN u.display_name END,
            'Unassigned'
        ) AS discipline_group,
        COALESCE(i.location_root, 'Unassigned') AS zone_root,
        SUM(CASE WHEN s.is_open = 1 THEN 1 ELSE 0 END) AS open_issues,
        SUM(CASE WHEN s.is_closed = 1 THEN 1 ELSE 0 END) AS closed_issues,
        COUNT(DISTINCT s.issue_sk) AS total_issues
    FROM fact.issue_snapshot s
    JOIN dim.date d ON s.snapshot_date_sk = d.date_sk
    JOIN dim.issue i ON s.issue_sk = i.issue_sk
    LEFT JOIN dim.project p ON s.project_sk = p.project_sk AND p.current_flag = 1
    LEFT JOIN discipline_pick dp ON i.issue_sk = dp.issue_sk
    LEFT JOIN dim.[user] u ON i.assignee_sk = u.user_sk AND u.current_flag = 1
    LEFT JOIN acc_issues ve
        ON i.source_system = 'ACC'
       AND CAST(ve.display_id AS NVARCHAR(255)) = i.issue_bk
       AND ve.rn = 1
    WHERE d.[date] >= @start_date
      AND d.[date] <= @end_date
    GROUP BY
        CAST(d.[date] AS date),
        COALESCE(p.project_bk, ve.pm_project_id, 0),
        COALESCE(p.client_sk, 0),
        COALESCE(p.project_type_sk, 0),
        CASE
            WHEN LOWER(ISNULL(COALESCE(s.status, i.status), '')) LIKE '%open%' THEN 'Open'
            WHEN LOWER(ISNULL(COALESCE(s.status, i.status), '')) LIKE '%progress%' THEN 'In progress'
            WHEN LOWER(ISNULL(COALESCE(s.status, i.status), '')) LIKE '%complete%' THEN 'Completed'
            WHEN LOWER(ISNULL(COALESCE(s.status, i.status), '')) LIKE '%close%' THEN 'Closed'
            ELSE 'Other'
        END,
        COALESCE(i.priority_normalized, 'Unassigned'),
        COALESCE(
            dp.discipline,
            CASE WHEN i.source_system = 'Revizto' THEN u.display_name END,
            'Unassigned'
        ),
        COALESCE(i.location_root, 'Unassigned');
END
GO
