/*
    Stored procedures orchestrating dimension, fact, bridge and mart loads.
    Procedures assume staging tables are populated with the latest extracts.
*/

USE [ProjectManagement];
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'warehouse')
BEGIN
    EXEC('CREATE SCHEMA warehouse AUTHORIZATION dbo;');
END
GO

/************************************************************
    DATE DIMENSION
************************************************************/
IF OBJECT_ID('warehouse.usp_load_dim_date', 'P') IS NOT NULL
    DROP PROCEDURE warehouse.usp_load_dim_date;
GO

CREATE PROCEDURE warehouse.usp_load_dim_date
    @StartDate DATE = '2015-01-01',
    @EndDate   DATE = '2035-12-31'
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @Current DATE = @StartDate;
    WHILE @Current <= @EndDate
    BEGIN
        DECLARE @DateSk INT = CONVERT(INT, FORMAT(@Current, 'yyyyMMdd'));
        IF NOT EXISTS (SELECT 1 FROM dim.date WHERE date_sk = @DateSk)
        BEGIN
            INSERT INTO dim.date (
                date_sk, [date], day_number_of_week, day_name,
                day_of_month, day_of_year, week_of_year, iso_week_of_year,
                week_start_date, month_number, month_name,
                quarter_number, year_number, fiscal_month_number,
                fiscal_quarter, fiscal_year, is_weekend, is_holiday
            )
            VALUES (
                @DateSk,
                @Current,
                DATEPART(WEEKDAY, @Current),
                DATENAME(WEEKDAY, @Current),
                DATEPART(DAY, @Current),
                DATEPART(DAYOFYEAR, @Current),
                DATEPART(WEEK, @Current),
                DATEPART(ISO_WEEK, @Current),
                DATEADD(DAY, 1 - DATEPART(WEEKDAY, @Current), @Current),
                DATEPART(MONTH, @Current),
                DATENAME(MONTH, @Current),
                DATEPART(QUARTER, @Current),
                DATEPART(YEAR, @Current),
                DATEPART(MONTH, @Current),
                DATEPART(QUARTER, @Current),
                DATEPART(YEAR, @Current),
                CASE WHEN DATEPART(WEEKDAY, @Current) IN (1,7) THEN 1 ELSE 0 END,
                0
            );
        END
        SET @Current = DATEADD(DAY, 1, @Current);
    END
END
GO

/************************************************************
    GENERIC SCD2 LOADER HELPERS
************************************************************/
IF OBJECT_ID('warehouse.usp_load_dim_client', 'P') IS NOT NULL
    DROP PROCEDURE warehouse.usp_load_dim_client;
GO

CREATE PROCEDURE warehouse.usp_load_dim_client
AS
BEGIN
    SET NOCOUNT ON;

    ;WITH latest AS (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY source_load_ts DESC) AS rn,
               HASHBYTES('SHA2_256',
                   CONCAT_WS('|',
                       ISNULL(client_name, ''),
                       ISNULL(contact_name, ''),
                       ISNULL(contact_email, ''),
                       ISNULL(industry_sector, ''),
                       ISNULL(country, '')
                   )
               ) AS row_hash
        FROM stg.clients
    )
    , dedup AS (
        SELECT client_id, client_name, contact_name, contact_email,
               industry_sector, country, row_hash
        FROM latest
        WHERE rn = 1
    )
    -- Close existing versions that changed
    UPDATE tgt
    SET current_flag = 0,
        effective_end = SYSUTCDATETIME()
    FROM dim.client tgt
    JOIN dedup src ON tgt.client_bk = src.client_id AND tgt.current_flag = 1
    WHERE tgt.record_hash <> src.row_hash;

    -- Insert new/changed versions
    INSERT INTO dim.client (
        client_bk, client_name, contact_name, contact_email,
        industry_sector, country, current_flag,
        effective_start, effective_end, record_hash, record_source
    )
    SELECT
        src.client_id,
        src.client_name,
        src.contact_name,
        src.contact_email,
        src.industry_sector,
        src.country,
        1,
        SYSUTCDATETIME(),
        NULL,
        src.row_hash,
        'stg.clients'
    FROM dedup src
    LEFT JOIN dim.client tgt
           ON tgt.client_bk = src.client_id AND tgt.current_flag = 1
    WHERE tgt.client_bk IS NULL OR tgt.record_hash <> src.row_hash;
END
GO

IF OBJECT_ID('warehouse.usp_load_dim_project_type', 'P') IS NOT NULL
    DROP PROCEDURE warehouse.usp_load_dim_project_type;
GO

CREATE PROCEDURE warehouse.usp_load_dim_project_type
AS
BEGIN
    SET NOCOUNT ON;

    ;WITH latest AS (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY project_type_id ORDER BY source_load_ts DESC) AS rn,
               HASHBYTES('SHA2_256',
                   CONCAT_WS('|',
                       ISNULL(project_type_name, ''),
                       ISNULL(category, '')
                   )
               ) AS row_hash
        FROM stg.project_types
    )
    , dedup AS (
        SELECT project_type_id, project_type_name, category, row_hash
        FROM latest
        WHERE rn = 1
    )
    UPDATE tgt
    SET current_flag = 0,
        effective_end = SYSUTCDATETIME()
    FROM dim.project_type tgt
    JOIN dedup src ON tgt.project_type_bk = src.project_type_id AND tgt.current_flag = 1
    WHERE tgt.record_hash <> src.row_hash;

    INSERT INTO dim.project_type (
        project_type_bk, project_type_name, category, current_flag,
        effective_start, effective_end, record_hash, record_source
    )
    SELECT
        src.project_type_id,
        src.project_type_name,
        src.category,
        1,
        SYSUTCDATETIME(),
        NULL,
        src.row_hash,
        'stg.project_types'
    FROM dedup src
    LEFT JOIN dim.project_type tgt
           ON tgt.project_type_bk = src.project_type_id AND tgt.current_flag = 1
    WHERE tgt.project_type_bk IS NULL OR tgt.record_hash <> src.row_hash;
END
GO

IF OBJECT_ID('warehouse.usp_load_dim_project', 'P') IS NOT NULL
    DROP PROCEDURE warehouse.usp_load_dim_project;
GO

CREATE PROCEDURE warehouse.usp_load_dim_project
AS
BEGIN
    SET NOCOUNT ON;

    ;WITH latest AS (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY project_id ORDER BY source_load_ts DESC) AS rn,
               HASHBYTES('SHA2_256',
                   CONCAT_WS('|',
                       ISNULL(project_name, ''),
                       ISNULL(CAST(client_id AS NVARCHAR(20)), ''),
                       ISNULL(CAST(project_type_id AS NVARCHAR(20)), ''),
                       ISNULL(status, ''),
                       ISNULL(priority, ''),
                       ISNULL(CONVERT(NVARCHAR(30), start_date, 126), ''),
                       ISNULL(CONVERT(NVARCHAR(30), end_date, 126), ''),
                       ISNULL(CONVERT(NVARCHAR(50), area_hectares), ''),
                       ISNULL(city, ''),
                       ISNULL(state, ''),
                       ISNULL(country, '')
                   )
               ) AS row_hash
        FROM stg.projects
    )
    , dedup AS (
        SELECT project_id, project_name, client_id, project_type_id, status, priority,
               start_date, end_date, area_hectares, city, state, country,
               created_at, updated_at, row_hash
        FROM latest
        WHERE rn = 1
    )
    UPDATE tgt
    SET current_flag = 0,
        effective_end = SYSUTCDATETIME()
    FROM dim.project tgt
    JOIN dedup src ON tgt.project_bk = src.project_id AND tgt.current_flag = 1
    WHERE tgt.record_hash <> src.row_hash;

    INSERT INTO dim.project (
        project_bk, project_name, client_sk, project_type_sk, status, priority,
        start_date, end_date, area_hectares, city, state, country,
        created_at, updated_at, current_flag,
        effective_start, effective_end, record_hash, record_source
    )
    SELECT
        src.project_id,
        src.project_name,
        tgt_client.client_sk,
        tgt_pt.project_type_sk,
        src.status,
        src.priority,
        src.start_date,
        src.end_date,
        src.area_hectares,
        src.city,
        src.state,
        src.country,
        src.created_at,
        src.updated_at,
        1,
        SYSUTCDATETIME(),
        NULL,
        src.row_hash,
        'stg.projects'
    FROM dedup src
    LEFT JOIN dim.project tgt
           ON tgt.project_bk = src.project_id AND tgt.current_flag = 1
    LEFT JOIN dim.client tgt_client ON tgt_client.client_bk = src.client_id AND tgt_client.current_flag = 1
    LEFT JOIN dim.project_type tgt_pt ON tgt_pt.project_type_bk = src.project_type_id AND tgt_pt.current_flag = 1
    WHERE tgt.project_bk IS NULL OR tgt.record_hash <> src.row_hash;
END
GO

IF OBJECT_ID('warehouse.usp_load_dim_issue_category', 'P') IS NOT NULL
    DROP PROCEDURE warehouse.usp_load_dim_issue_category;
GO

CREATE PROCEDURE warehouse.usp_load_dim_issue_category
AS
BEGIN
    SET NOCOUNT ON;

    ;WITH latest AS (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY category_id ORDER BY source_load_ts DESC) AS rn,
               HASHBYTES('SHA2_256',
                   CONCAT_WS('|',
                       ISNULL(category_name, ''),
                       ISNULL(CONVERT(NVARCHAR(20), parent_category_id), ''),
                       ISNULL(CONVERT(NVARCHAR(5), category_level), ''),
                       ISNULL(description, '')
                   )
               ) AS row_hash
        FROM stg.issue_categories
    )
    , dedup AS (
        SELECT category_id, category_name, parent_category_id, category_level, description, row_hash
        FROM latest WHERE rn = 1
    )
    UPDATE tgt
    SET current_flag = 0,
        effective_end = SYSUTCDATETIME()
    FROM dim.issue_category tgt
    JOIN dedup src ON tgt.category_bk = src.category_id AND tgt.current_flag = 1
    WHERE tgt.record_hash <> src.row_hash;

    INSERT INTO dim.issue_category (
        category_bk, category_name, parent_category_sk, category_level,
        description, lineage_path, level1_name, level2_name, level3_name,
        current_flag, effective_start, effective_end, record_hash, record_source
    )
    SELECT
        src.category_id,
        src.category_name,
        parent_dim.issue_category_sk,
        src.category_level,
        src.description,
        NULL,
        CASE WHEN src.category_level >= 1 THEN src.category_name END,
        NULL,
        NULL,
        1,
        SYSUTCDATETIME(),
        NULL,
        src.row_hash,
        'stg.issue_categories'
    FROM dedup src
    LEFT JOIN dim.issue_category tgt
           ON tgt.category_bk = src.category_id AND tgt.current_flag = 1
    LEFT JOIN dim.issue_category parent_dim
           ON parent_dim.category_bk = src.parent_category_id
          AND parent_dim.current_flag = 1
    WHERE tgt.category_bk IS NULL OR tgt.record_hash <> src.row_hash;
END
GO

IF OBJECT_ID('warehouse.usp_load_dim_user', 'P') IS NOT NULL
    DROP PROCEDURE warehouse.usp_load_dim_user;
GO

CREATE PROCEDURE warehouse.usp_load_dim_user
AS
BEGIN
    SET NOCOUNT ON;

    ;WITH latest AS (
        SELECT
            assignee AS user_name,
            source_system,
            MAX(source_load_ts) AS max_ts
        FROM stg.issues
        WHERE assignee IS NOT NULL
        GROUP BY assignee, source_system
    )
    INSERT INTO dim.[user] (
        user_bk, display_name, email, source_system,
        role, current_flag, effective_start, effective_end,
        record_hash, record_source
    )
    SELECT
        l.user_name,
        l.user_name,
        NULL,
        l.source_system,
        NULL,
        1,
        SYSUTCDATETIME(),
        NULL,
        HASHBYTES('SHA2_256', CONCAT_WS('|', l.user_name, l.source_system)),
        'stg.issues'
    FROM latest l
    LEFT JOIN dim.[user] u
           ON u.user_bk = l.user_name
          AND u.source_system = l.source_system
          AND u.current_flag = 1
    WHERE u.user_sk IS NULL;
END
GO

IF OBJECT_ID('warehouse.usp_load_dim_issue', 'P') IS NOT NULL
    DROP PROCEDURE warehouse.usp_load_dim_issue;
GO

CREATE PROCEDURE warehouse.usp_load_dim_issue
AS
BEGIN
    SET NOCOUNT ON;

    ;WITH latest AS (
        SELECT
            i.source_system,
            i.issue_id,
            ROW_NUMBER() OVER (
                PARTITION BY i.source_system, i.issue_id
                ORDER BY i.source_load_ts DESC
            ) AS rn,
            i.project_name,
            i.project_id_raw,
            i.status,
            i.priority,
            i.title,
            i.assignee,
            i.author,
            i.created_at,
            i.closed_at,
            p.project_sk,
            ac.issue_category_sk AS primary_category_sk,
            dc.issue_category_sk AS discipline_category_sk,
            HASHBYTES('SHA2_256',
                CONCAT_WS('|',
                    ISNULL(i.project_id_raw, ''),
                    ISNULL(i.status, ''),
                    ISNULL(i.priority, ''),
                    ISNULL(i.title, ''),
                    ISNULL(i.assignee, ''),
                    ISNULL(i.author, ''),
                    ISNULL(CONVERT(NVARCHAR(30), i.created_at, 126), ''),
                    ISNULL(CONVERT(NVARCHAR(30), i.closed_at, 126), ''),
                    ISNULL(CONVERT(NVARCHAR(20), ac.issue_category_sk), ''),
                    ISNULL(CONVERT(NVARCHAR(20), dc.issue_category_sk), '')
                )
            ) AS row_hash
        FROM stg.issues i
        LEFT JOIN dim.project p ON p.project_name = i.project_name AND p.current_flag = 1
        LEFT JOIN dim.issue_category ac ON ac.category_name = i.category_primary AND ac.current_flag = 1
        LEFT JOIN dim.issue_category dc ON dc.category_name = i.discipline AND dc.current_flag = 1
    )
    , dedup AS (
        SELECT *
        FROM latest
        WHERE rn = 1
    )
    UPDATE tgt
    SET current_flag = 0,
        effective_end = SYSUTCDATETIME()
    FROM dim.issue tgt
    JOIN dedup src
      ON tgt.issue_bk = src.issue_id
     AND tgt.source_system = src.source_system
     AND tgt.current_flag = 1
    WHERE tgt.record_hash <> src.row_hash;

    INSERT INTO dim.issue (
        issue_bk, source_system, project_sk, title, status, priority,
        assignee_sk, author_sk, created_date_sk, closed_date_sk,
        discipline_category_sk, primary_category_sk, secondary_category_sk,
        current_flag, effective_start, effective_end, record_hash, record_source
    )
    SELECT
        src.issue_id,
        src.source_system,
        src.project_sk,
        src.title,
        src.status,
        src.priority,
        assignee.user_sk,
        author.user_sk,
        CASE WHEN src.created_at IS NOT NULL THEN CONVERT(INT, FORMAT(src.created_at, 'yyyyMMdd')) END,
        CASE WHEN src.closed_at IS NOT NULL THEN CONVERT(INT, FORMAT(src.closed_at, 'yyyyMMdd')) END,
        src.discipline_category_sk,
        src.primary_category_sk,
        NULL,
        1,
        SYSUTCDATETIME(),
        NULL,
        src.row_hash,
        'stg.issues'
    FROM dedup src
    LEFT JOIN dim.issue tgt
           ON tgt.issue_bk = src.issue_id
          AND tgt.source_system = src.source_system
          AND tgt.current_flag = 1
    LEFT JOIN dim.[user] assignee
           ON assignee.user_bk = src.assignee
          AND assignee.source_system = src.source_system
          AND assignee.current_flag = 1
    LEFT JOIN dim.[user] author
           ON author.user_bk = src.author
          AND author.source_system = src.source_system
          AND author.current_flag = 1
    WHERE tgt.issue_sk IS NULL OR tgt.record_hash <> src.row_hash;
END
GO

IF OBJECT_ID('warehouse.usp_load_dim_service', 'P') IS NOT NULL
    DROP PROCEDURE warehouse.usp_load_dim_service;
GO

CREATE PROCEDURE warehouse.usp_load_dim_service
AS
BEGIN
    SET NOCOUNT ON;

    ;WITH latest AS (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY service_id ORDER BY source_load_ts DESC) AS rn,
               HASHBYTES('SHA2_256',
                   CONCAT_WS('|',
                       ISNULL(CAST(project_id AS NVARCHAR(20)), ''),
                       ISNULL(service_code, ''),
                       ISNULL(service_name, ''),
                       ISNULL(phase, ''),
                       ISNULL(unit_type, ''),
                       ISNULL(CONVERT(NVARCHAR(30), unit_qty), ''),
                       ISNULL(CONVERT(NVARCHAR(30), unit_rate), ''),
                       ISNULL(CONVERT(NVARCHAR(30), lump_sum_fee), ''),
                       ISNULL(CONVERT(NVARCHAR(30), agreed_fee), ''),
                       ISNULL(CONVERT(NVARCHAR(30), progress_pct), ''),
                       ISNULL(CONVERT(NVARCHAR(30), claimed_to_date), ''),
                       ISNULL(status, '')
                   )
               ) AS row_hash
        FROM stg.project_services
    )
    , dedup AS (
        SELECT *
        FROM latest
        WHERE rn = 1
    )
    UPDATE tgt
    SET current_flag = 0,
        effective_end = SYSUTCDATETIME()
    FROM dim.service tgt
    JOIN dedup src ON tgt.service_bk = src.service_id AND tgt.current_flag = 1
    WHERE tgt.record_hash <> src.row_hash;

    INSERT INTO dim.service (
        service_bk, project_sk, service_code, service_name, phase, unit_type,
        unit_qty, unit_rate, lump_sum_fee, agreed_fee, progress_pct, status, current_flag,
        effective_start, effective_end, record_hash, record_source
    )
    SELECT
        src.service_id,
        proj.project_sk,
        src.service_code,
        src.service_name,
        src.phase,
        src.unit_type,
        src.unit_qty,
        src.unit_rate,
        src.lump_sum_fee,
        src.agreed_fee,
        src.progress_pct,
        src.status,
        1,
        SYSUTCDATETIME(),
        NULL,
        src.row_hash,
        'stg.project_services'
    FROM dedup src
    LEFT JOIN dim.service tgt
           ON tgt.service_bk = src.service_id AND tgt.current_flag = 1
    LEFT JOIN dim.project proj
           ON proj.project_bk = src.project_id AND proj.current_flag = 1
    WHERE tgt.service_bk IS NULL OR tgt.record_hash <> src.row_hash;
END
GO

IF OBJECT_ID('warehouse.usp_load_dim_review_stage', 'P') IS NOT NULL
    DROP PROCEDURE warehouse.usp_load_dim_review_stage;
GO

CREATE PROCEDURE warehouse.usp_load_dim_review_stage
AS
BEGIN
    SET NOCOUNT ON;

    -- Placeholder: stage data not yet staged; ensure table exists.
    -- In future, integrate ReviewStages staging feeds.
END
GO

IF OBJECT_ID('warehouse.usp_load_dim_review_cycle', 'P') IS NOT NULL
    DROP PROCEDURE warehouse.usp_load_dim_review_cycle;
GO

CREATE PROCEDURE warehouse.usp_load_dim_review_cycle
AS
BEGIN
    SET NOCOUNT ON;

    ;WITH latest AS (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY review_id ORDER BY source_load_ts DESC) AS rn,
               HASHBYTES('SHA2_256',
                   CONCAT_WS('|',
                       ISNULL(CAST(service_id AS NVARCHAR(20)), ''),
                       ISNULL(CAST(cycle_no AS NVARCHAR(10)), ''),
                       ISNULL(CONVERT(NVARCHAR(30), planned_date, 126), ''),
                       ISNULL(CONVERT(NVARCHAR(30), due_date, 126), ''),
                       ISNULL(CONVERT(NVARCHAR(30), actual_date, 126), ''),
                       ISNULL(status, ''),
                       ISNULL(CONVERT(NVARCHAR(30), weight_factor), '')
                   )
               ) AS row_hash
        FROM stg.service_reviews
    )
    , dedup AS (
        SELECT *
        FROM latest
        WHERE rn = 1
    )
    UPDATE tgt
    SET current_flag = 0,
        effective_end = SYSUTCDATETIME()
    FROM dim.review_cycle tgt
    JOIN dedup src ON tgt.review_bk = src.review_id AND tgt.current_flag = 1
    WHERE tgt.record_hash <> src.row_hash;

    INSERT INTO dim.review_cycle (
        review_bk, service_sk, project_sk, cycle_no,
        planned_date_sk, due_date_sk, stage_sk, weight_factor,
        status, current_flag, effective_start, effective_end,
        record_hash, record_source
    )
    SELECT
        src.review_id,
        svc.service_sk,
        svc.project_sk,
        src.cycle_no,
        CASE WHEN src.planned_date IS NOT NULL THEN CONVERT(INT, FORMAT(src.planned_date, 'yyyyMMdd')) END,
        CASE WHEN src.due_date IS NOT NULL THEN CONVERT(INT, FORMAT(src.due_date, 'yyyyMMdd')) END,
        NULL,
        src.weight_factor,
        src.status,
        1,
        SYSUTCDATETIME(),
        NULL,
        src.row_hash,
        'stg.service_reviews'
    FROM dedup src
    LEFT JOIN dim.review_cycle tgt
           ON tgt.review_bk = src.review_id AND tgt.current_flag = 1
    LEFT JOIN dim.service svc
           ON svc.service_bk = src.service_id AND svc.current_flag = 1
    WHERE tgt.review_bk IS NULL OR tgt.record_hash <> src.row_hash;
END
GO

/************************************************************
    FACT LOADERS (simplified prototypes)
************************************************************/
IF OBJECT_ID('warehouse.usp_load_fact_issue_snapshot', 'P') IS NOT NULL
    DROP PROCEDURE warehouse.usp_load_fact_issue_snapshot;
GO

CREATE PROCEDURE warehouse.usp_load_fact_issue_snapshot
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @SnapshotDateSk INT = CONVERT(INT, FORMAT(SYSUTCDATETIME(), 'yyyyMMdd'));

    INSERT INTO fact.issue_snapshot (
        snapshot_date_sk, issue_sk, project_sk, client_sk, project_type_sk,
        status, is_open, is_closed, backlog_age_days, resolution_days,
        urgency_score, complexity_score, sentiment_score, comment_count,
        high_priority_flag, record_source
    )
    SELECT
        @SnapshotDateSk,
        issue.issue_sk,
        issue.project_sk,
        proj.client_sk,
        proj.project_type_sk,
        issue.status,
        CASE WHEN issue.status IN ('open', 'in_progress') THEN 1 ELSE 0 END,
        CASE WHEN issue.status IN ('closed') THEN 1 ELSE 0 END,
        CASE
            WHEN issue.created_date_sk IS NOT NULL
            THEN DATEDIFF(DAY,
                CAST(CONVERT(VARCHAR(8), issue.created_date_sk) AS DATE),
                CAST(CONVERT(VARCHAR(8), @SnapshotDateSk) AS DATE)
            )
            ELSE NULL
        END,
        proc_issue.resolution_days,
        proc_issue.urgency_score,
        proc_issue.complexity_score,
        proc_issue.sentiment_score,
        proc_issue.comment_count,
        CASE WHEN issue.priority IN ('critical', 'high') THEN 1 ELSE 0 END,
        'warehouse.usp_load_fact_issue_snapshot'
    FROM dim.issue issue
    LEFT JOIN fact.issue_snapshot existing
           ON existing.issue_sk = issue.issue_sk AND existing.snapshot_date_sk = @SnapshotDateSk
    LEFT JOIN dim.project proj ON issue.project_sk = proj.project_sk
    LEFT JOIN stg.processed_issues proc_issue
           ON proc_issue.issue_id = issue.issue_bk
          AND proc_issue.source_system = issue.source_system
    WHERE existing.issue_snapshot_sk IS NULL;
END
GO

IF OBJECT_ID('warehouse.usp_load_fact_issue_activity', 'P') IS NOT NULL
    DROP PROCEDURE warehouse.usp_load_fact_issue_activity;
GO

CREATE PROCEDURE warehouse.usp_load_fact_issue_activity
AS
BEGIN
    SET NOCOUNT ON;

    -- Example activity: newly closed issues today.
    DECLARE @Today DATE = CAST(SYSUTCDATETIME() AS DATE);

    INSERT INTO fact.issue_activity (
        issue_sk, event_type, event_date_sk, event_ts, status_from, status_to,
        project_sk, record_source
    )
    SELECT
        issue.issue_sk,
        'status_change',
        CONVERT(INT, FORMAT(@Today, 'yyyyMMdd')),
        SYSUTCDATETIME(),
        'open',
        'closed',
        issue.project_sk,
        'warehouse.usp_load_fact_issue_activity'
    FROM dim.issue issue
    WHERE issue.closed_date_sk = CONVERT(INT, FORMAT(@Today, 'yyyyMMdd'))
      AND NOT EXISTS (
            SELECT 1
            FROM fact.issue_activity fa
            WHERE fa.issue_sk = issue.issue_sk
              AND fa.event_date_sk = CONVERT(INT, FORMAT(@Today, 'yyyyMMdd'))
              AND fa.event_type = 'status_change'
        );
END
GO

IF OBJECT_ID('warehouse.usp_load_fact_service_monthly', 'P') IS NOT NULL
    DROP PROCEDURE warehouse.usp_load_fact_service_monthly;
GO

CREATE PROCEDURE warehouse.usp_load_fact_service_monthly
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @MonthSk INT = CONVERT(INT, FORMAT(SYSUTCDATETIME(), 'yyyyMM01'));

    INSERT INTO fact.service_monthly (
        service_sk, project_sk, client_sk, project_type_sk, month_date_sk,
        planned_quantity, actual_quantity, planned_fee, earned_value,
        claimed_to_date, variance_fee, progress_pct, status, record_source
    )
    SELECT
        svc.service_sk,
        svc.project_sk,
        proj.client_sk,
        proj.project_type_sk,
        @MonthSk,
        svc.unit_qty,
        NULL,
        svc.agreed_fee,
        svc.agreed_fee * (svc.progress_pct / 100.0),
        svc.lump_sum_fee,
        (svc.agreed_fee * (svc.progress_pct / 100.0)) - svc.lump_sum_fee,
        svc.progress_pct,
        svc.status,
        'warehouse.usp_load_fact_service_monthly'
    FROM dim.service svc
    JOIN dim.project proj ON svc.project_sk = proj.project_sk
    WHERE NOT EXISTS (
        SELECT 1
        FROM fact.service_monthly fm
        WHERE fm.service_sk = svc.service_sk
          AND fm.month_date_sk = @MonthSk
    );
END
GO

IF OBJECT_ID('warehouse.usp_load_fact_review_cycle', 'P') IS NOT NULL
    DROP PROCEDURE warehouse.usp_load_fact_review_cycle;
GO

CREATE PROCEDURE warehouse.usp_load_fact_review_cycle
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO fact.review_cycle (
        review_cycle_sk, service_sk, project_sk, client_sk, project_type_sk,
        planned_date_sk, due_date_sk, actual_date_sk, planned_vs_actual_days,
        is_completed, is_overdue, status, weight_factor,
        issue_count_window, issue_closed_window, record_source
    )
    SELECT
        rc.review_cycle_sk,
        rc.service_sk,
        svc.project_sk,
        proj.client_sk,
        proj.project_type_sk,
        rc.planned_date_sk,
        rc.due_date_sk,
        NULL,
        NULL,
        CASE WHEN rc.status = 'completed' THEN 1 ELSE 0 END,
        CASE WHEN rc.status = 'overdue' THEN 1 ELSE 0 END,
        rc.status,
        rc.weight_factor,
        NULL,
        NULL,
        'warehouse.usp_load_fact_review_cycle'
    FROM dim.review_cycle rc
    JOIN dim.service svc ON rc.service_sk = svc.service_sk
    JOIN dim.project proj ON svc.project_sk = proj.project_sk
    WHERE NOT EXISTS (
        SELECT 1
        FROM fact.review_cycle fr
        WHERE fr.review_cycle_sk = rc.review_cycle_sk
    );
END
GO

IF OBJECT_ID('warehouse.usp_load_fact_review_event', 'P') IS NOT NULL
    DROP PROCEDURE warehouse.usp_load_fact_review_event;
GO

CREATE PROCEDURE warehouse.usp_load_fact_review_event
AS
BEGIN
    SET NOCOUNT ON;
    -- Placeholder for future review event capture.
END
GO

IF OBJECT_ID('warehouse.usp_load_fact_project_kpi_monthly', 'P') IS NOT NULL
    DROP PROCEDURE warehouse.usp_load_fact_project_kpi_monthly;
GO

CREATE PROCEDURE warehouse.usp_load_fact_project_kpi_monthly
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @MonthSk INT = CONVERT(INT, FORMAT(SYSUTCDATETIME(), 'yyyyMM01'));

    DECLARE @MonthStart DATE = CONVERT(DATE, CONVERT(VARCHAR(8), @MonthSk));
    DECLARE @MonthEnd DATE = EOMONTH(@MonthStart);
    DECLARE @MonthStartSk INT = CONVERT(INT, FORMAT(@MonthStart, 'yyyyMMdd'));
    DECLARE @MonthEndSk INT = CONVERT(INT, FORMAT(@MonthEnd, 'yyyyMMdd'));

    INSERT INTO fact.project_kpi_monthly (
        project_sk, client_sk, project_type_sk, month_date_sk,
        total_issues, open_issues, closed_issues, high_priority_issues,
        avg_resolution_days, review_count, completed_reviews,
        overdue_reviews, services_in_progress, services_completed,
        earned_value, claimed_to_date, variance_fee, record_source
    )
    SELECT
        proj.project_sk,
        proj.client_sk,
        proj.project_type_sk,
        @MonthSk,
        COUNT(*) AS total_issues,
        SUM(CASE WHEN snapshot.is_open = 1 THEN 1 ELSE 0 END) AS open_issues,
        SUM(CASE WHEN snapshot.is_closed = 1 THEN 1 ELSE 0 END) AS closed_issues,
        SUM(CASE WHEN snapshot.high_priority_flag = 1 THEN 1 ELSE 0 END) AS high_priority_issues,
        AVG(CAST(snapshot.resolution_days AS DECIMAL(9,2))) AS avg_resolution_days,
        NULL AS review_count,
        NULL AS completed_reviews,
        NULL AS overdue_reviews,
        SUM(CASE WHEN svc.status = 'in_progress' THEN 1 ELSE 0 END) AS services_in_progress,
        SUM(CASE WHEN svc.status = 'completed' THEN 1 ELSE 0 END) AS services_completed,
        SUM(ISNULL(service_month.earned_value, 0)) AS earned_value,
        SUM(ISNULL(service_month.claimed_to_date, 0)) AS claimed_to_date,
        SUM(ISNULL(service_month.variance_fee, 0)) AS variance_fee,
        'warehouse.usp_load_fact_project_kpi_monthly'
    FROM fact.issue_snapshot snapshot
    JOIN dim.project proj ON snapshot.project_sk = proj.project_sk
    LEFT JOIN fact.service_monthly service_month
        ON service_month.project_sk = proj.project_sk
       AND service_month.month_date_sk = @MonthSk
    LEFT JOIN dim.service svc
        ON svc.service_sk = service_month.service_sk
    WHERE snapshot.snapshot_date_sk BETWEEN @MonthStartSk AND @MonthEndSk
      AND NOT EXISTS (
            SELECT 1
            FROM fact.project_kpi_monthly existing
            WHERE existing.project_sk = proj.project_sk
              AND existing.month_date_sk = @MonthSk
        )
    GROUP BY proj.project_sk, proj.client_sk, proj.project_type_sk;
END
GO

IF OBJECT_ID('warehouse.usp_load_bridges', 'P') IS NOT NULL
    DROP PROCEDURE warehouse.usp_load_bridges;
GO

CREATE PROCEDURE warehouse.usp_load_bridges
AS
BEGIN
    SET NOCOUNT ON;

    -- Issue category bridge
    INSERT INTO brg.issue_category (issue_sk, issue_category_sk, category_role)
    SELECT DISTINCT
        issue.issue_sk,
        issue.discipline_category_sk,
        'discipline'
    FROM dim.issue issue
    WHERE issue.discipline_category_sk IS NOT NULL
      AND NOT EXISTS (
            SELECT 1
            FROM brg.issue_category bic
            WHERE bic.issue_sk = issue.issue_sk
              AND bic.issue_category_sk = issue.discipline_category_sk
              AND bic.category_role = 'discipline'
        );
END
GO
