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

    IF OBJECT_ID('tempdb..#dedup') IS NOT NULL DROP TABLE #dedup;

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
    SELECT client_id, client_name, contact_name, contact_email,
           industry_sector, country, row_hash
    INTO #dedup
    FROM latest
    WHERE rn = 1;
    -- Close existing versions that changed
    UPDATE tgt
    SET current_flag = 0,
        effective_end = SYSUTCDATETIME()
    FROM dim.client tgt
    JOIN #dedup src ON tgt.client_bk = src.client_id AND tgt.current_flag = 1
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
    FROM #dedup src
    LEFT JOIN dim.client tgt
           ON tgt.client_bk = src.client_id AND tgt.current_flag = 1
    WHERE tgt.client_bk IS NULL OR tgt.record_hash <> src.row_hash;
    DROP TABLE IF EXISTS #dedup;
END
GO

IF OBJECT_ID('warehouse.usp_load_dim_project_type', 'P') IS NOT NULL
    DROP PROCEDURE warehouse.usp_load_dim_project_type;
GO

CREATE PROCEDURE warehouse.usp_load_dim_project_type
AS
BEGIN
    SET NOCOUNT ON;

    IF OBJECT_ID('tempdb..#dedup') IS NOT NULL DROP TABLE #dedup;

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
    SELECT project_type_id, project_type_name, category, row_hash
    INTO #dedup
    FROM latest
    WHERE rn = 1;
    UPDATE tgt
    SET current_flag = 0,
        effective_end = SYSUTCDATETIME()
    FROM dim.project_type tgt
    JOIN #dedup src ON tgt.project_type_bk = src.project_type_id AND tgt.current_flag = 1
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
    FROM #dedup src
    LEFT JOIN dim.project_type tgt
           ON tgt.project_type_bk = src.project_type_id AND tgt.current_flag = 1
    WHERE tgt.project_type_bk IS NULL OR tgt.record_hash <> src.row_hash;
    DROP TABLE IF EXISTS #dedup;
END
GO

IF OBJECT_ID('warehouse.usp_load_dim_project', 'P') IS NOT NULL
    DROP PROCEDURE warehouse.usp_load_dim_project;
GO

CREATE PROCEDURE warehouse.usp_load_dim_project
AS
BEGIN
    SET NOCOUNT ON;

    IF OBJECT_ID('tempdb..#dedup') IS NOT NULL DROP TABLE #dedup;

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
    SELECT project_id, project_name, client_id, project_type_id, status, priority,
           start_date, end_date, area_hectares, city, state, country,
           created_at, updated_at, row_hash
    INTO #dedup
    FROM latest
    WHERE rn = 1;
    UPDATE tgt
    SET current_flag = 0,
        effective_end = SYSUTCDATETIME()
    FROM dim.project tgt
    JOIN #dedup src ON tgt.project_bk = src.project_id AND tgt.current_flag = 1
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
    FROM #dedup src
    LEFT JOIN dim.project tgt
           ON tgt.project_bk = src.project_id AND tgt.current_flag = 1
    LEFT JOIN dim.client tgt_client ON tgt_client.client_bk = src.client_id AND tgt_client.current_flag = 1
    LEFT JOIN dim.project_type tgt_pt ON tgt_pt.project_type_bk = src.project_type_id AND tgt_pt.current_flag = 1
    WHERE tgt.project_bk IS NULL OR tgt.record_hash <> src.row_hash;
    DROP TABLE IF EXISTS #dedup;
END
GO

IF OBJECT_ID('warehouse.usp_load_dim_project_alias', 'P') IS NOT NULL
    DROP PROCEDURE warehouse.usp_load_dim_project_alias;
GO

CREATE PROCEDURE warehouse.usp_load_dim_project_alias
AS
BEGIN
    SET NOCOUNT ON;

    IF OBJECT_ID('tempdb..#alias_dedup') IS NOT NULL DROP TABLE #alias_dedup;

    ;WITH latest AS (
        SELECT
            pa.pm_project_id,
            pa.alias_name,
            pa.alias_type,
            ROW_NUMBER() OVER (
                PARTITION BY pa.pm_project_id, pa.alias_name
                ORDER BY pa.source_load_ts DESC
            ) AS rn,
            HASHBYTES(
                'SHA2_256',
                CONCAT_WS(
                    '|',
                    ISNULL(pa.alias_name, ''),
                    ISNULL(pa.alias_type, ''),
                    ISNULL(CONVERT(NVARCHAR(20), pa.pm_project_id), '')
                )
            ) AS row_hash
        FROM stg.project_aliases pa
    )
    SELECT
        l.pm_project_id,
        l.alias_name,
        l.alias_type,
        l.row_hash,
        proj.project_sk
    INTO #alias_dedup
    FROM latest l
    JOIN dim.project proj
         ON proj.project_bk = l.pm_project_id
        AND proj.current_flag = 1
    WHERE l.rn = 1;

    UPDATE tgt
    SET current_flag = 0,
        effective_end = SYSUTCDATETIME()
    FROM dim.project_alias tgt
    JOIN #alias_dedup src
      ON tgt.pm_project_id = src.pm_project_id
     AND tgt.alias_name = src.alias_name
     AND tgt.current_flag = 1
    WHERE tgt.record_hash <> src.row_hash;

    INSERT INTO dim.project_alias (
        pm_project_id,
        alias_name,
        alias_type,
        project_sk,
        current_flag,
        effective_start,
        effective_end,
        record_hash,
        record_source
    )
    SELECT
        src.pm_project_id,
        src.alias_name,
        src.alias_type,
        src.project_sk,
        1,
        SYSUTCDATETIME(),
        NULL,
        src.row_hash,
        'stg.project_aliases'
    FROM #alias_dedup src
    LEFT JOIN dim.project_alias tgt
           ON tgt.pm_project_id = src.pm_project_id
          AND tgt.alias_name = src.alias_name
          AND tgt.current_flag = 1
    WHERE tgt.project_alias_sk IS NULL OR tgt.record_hash <> src.row_hash;

    DROP TABLE IF EXISTS #alias_dedup;
END
GO

IF OBJECT_ID('warehouse.usp_load_dim_issue_category', 'P') IS NOT NULL
    DROP PROCEDURE warehouse.usp_load_dim_issue_category;
GO

CREATE PROCEDURE warehouse.usp_load_dim_issue_category
AS
BEGIN
    SET NOCOUNT ON;

    IF OBJECT_ID('tempdb..#dedup') IS NOT NULL DROP TABLE #dedup;

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
    SELECT category_id, category_name, parent_category_id, category_level, description, row_hash
    INTO #dedup
    FROM latest WHERE rn = 1;
    UPDATE tgt
    SET current_flag = 0,
        effective_end = SYSUTCDATETIME()
    FROM dim.issue_category tgt
    JOIN #dedup src ON tgt.category_bk = src.category_id AND tgt.current_flag = 1
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
    FROM #dedup src
    LEFT JOIN dim.issue_category tgt
           ON tgt.category_bk = src.category_id AND tgt.current_flag = 1
    LEFT JOIN dim.issue_category parent_dim
           ON parent_dim.category_bk = src.parent_category_id
          AND parent_dim.current_flag = 1
    WHERE tgt.category_bk IS NULL OR tgt.record_hash <> src.row_hash;
    DROP TABLE IF EXISTS #dedup;
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

    IF OBJECT_ID('tempdb..#dedup') IS NOT NULL DROP TABLE #dedup;

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
            i.priority_normalized,
            i.title,
            i.assignee,
            i.author,
            i.created_at,
            i.closed_at,
            i.location_raw,
            i.location_root,
            i.location_building,
            i.location_level,
            COALESCE(p_id.project_sk, palias.project_sk, p_name.project_sk) AS project_sk,
            ac.issue_category_sk AS primary_category_sk,
            dc.issue_category_sk AS discipline_category_sk,
            HASHBYTES('SHA2_256',
                CONCAT_WS('|',
                    ISNULL(i.project_id_raw, ''),
                    ISNULL(CONVERT(NVARCHAR(20), COALESCE(p_id.project_sk, palias.project_sk, p_name.project_sk)), ''),
                    ISNULL(i.status, ''),
                    ISNULL(i.priority, ''),
                    ISNULL(i.priority_normalized, ''),
                    ISNULL(i.title, ''),
                    ISNULL(i.assignee, ''),
                    ISNULL(i.author, ''),
                    ISNULL(CONVERT(NVARCHAR(30), i.created_at, 126), ''),
                    ISNULL(CONVERT(NVARCHAR(30), i.closed_at, 126), ''),
                    ISNULL(CONVERT(NVARCHAR(20), ac.issue_category_sk), ''),
                    ISNULL(CONVERT(NVARCHAR(20), dc.issue_category_sk), ''),
                    ISNULL(i.location_raw, ''),
                    ISNULL(i.location_root, ''),
                    ISNULL(i.location_building, ''),
                    ISNULL(i.location_level, '')
                )
            ) AS row_hash
     FROM stg.issues i
     LEFT JOIN dim.project p_id
         ON p_id.project_bk = TRY_CONVERT(INT, i.project_id_raw)
        AND p_id.current_flag = 1
     LEFT JOIN dim.project_alias palias
         ON palias.alias_name = i.project_name
        AND palias.current_flag = 1
     LEFT JOIN dim.project p_name
         ON p_name.project_name = i.project_name
        AND p_name.current_flag = 1
        OUTER APPLY (
            SELECT TOP (1) m.normalized_discipline
            FROM dbo.issue_discipline_map m
            WHERE m.source_system = i.source_system
              AND m.raw_discipline = i.discipline
              AND m.active_flag = 1
              AND (m.project_id = i.project_id_raw OR m.project_id IS NULL)
            ORDER BY CASE WHEN m.project_id = i.project_id_raw THEN 0 ELSE 1 END,
                     CASE WHEN m.is_default = 1 THEN 0 ELSE 1 END
        ) dm
        LEFT JOIN dim.issue_category ac ON ac.category_name = i.category_primary AND ac.current_flag = 1
        LEFT JOIN dim.issue_category dc ON dc.category_name = COALESCE(dm.normalized_discipline, i.discipline) AND dc.current_flag = 1
    )
    SELECT *
    INTO #dedup
    FROM latest
    WHERE rn = 1;
    UPDATE tgt
    SET current_flag = 0,
        effective_end = SYSUTCDATETIME()
        FROM dim.issue tgt
        JOIN #dedup src
      ON tgt.issue_bk = src.issue_id
     AND tgt.source_system = src.source_system
     AND tgt.current_flag = 1
    WHERE tgt.record_hash <> src.row_hash;

    INSERT INTO dim.issue (
        issue_bk, source_system, project_sk, title, status, priority, priority_normalized,
        assignee_sk, author_sk, created_date_sk, closed_date_sk,
        discipline_category_sk, primary_category_sk, secondary_category_sk,
        location_raw, location_root, location_building, location_level,
        current_flag, effective_start, effective_end, record_hash, record_source
    )
    SELECT
        src.issue_id,
        src.source_system,
        src.project_sk,
        src.title,
        src.status,
        src.priority,
        src.priority_normalized,
        assignee.user_sk,
        author.user_sk,
        CASE WHEN src.created_at IS NOT NULL THEN CONVERT(INT, FORMAT(src.created_at, 'yyyyMMdd')) END,
        CASE WHEN src.closed_at IS NOT NULL THEN CONVERT(INT, FORMAT(src.closed_at, 'yyyyMMdd')) END,
        src.discipline_category_sk,
        src.primary_category_sk,
        NULL,
        src.location_raw,
        src.location_root,
        src.location_building,
        src.location_level,
        1,
        SYSUTCDATETIME(),
        NULL,
        src.row_hash,
        'stg.issues'
    FROM #dedup src
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
    DROP TABLE IF EXISTS #dedup;
END
GO

IF OBJECT_ID('warehouse.usp_load_dim_service', 'P') IS NOT NULL
    DROP PROCEDURE warehouse.usp_load_dim_service;
GO

CREATE PROCEDURE warehouse.usp_load_dim_service
AS
BEGIN
    SET NOCOUNT ON;

    IF OBJECT_ID('tempdb..#dedup') IS NOT NULL DROP TABLE #dedup;

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
    SELECT *
    INTO #dedup
    FROM latest
    WHERE rn = 1;
    UPDATE tgt
    SET current_flag = 0,
        effective_end = SYSUTCDATETIME()
    FROM dim.service tgt
    JOIN #dedup src ON tgt.service_bk = src.service_id AND tgt.current_flag = 1
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
    FROM #dedup src
    LEFT JOIN dim.service tgt
           ON tgt.service_bk = src.service_id AND tgt.current_flag = 1
    LEFT JOIN dim.project proj
           ON proj.project_bk = src.project_id AND proj.current_flag = 1
    WHERE tgt.service_bk IS NULL OR tgt.record_hash <> src.row_hash;
    DROP TABLE IF EXISTS #dedup;
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

    IF OBJECT_ID('tempdb..#dedup') IS NOT NULL DROP TABLE #dedup;

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
    SELECT *
    INTO #dedup
    FROM latest
    WHERE rn = 1;
    UPDATE tgt
    SET current_flag = 0,
        effective_end = SYSUTCDATETIME()
    FROM dim.review_cycle tgt
    JOIN #dedup src ON tgt.review_bk = src.review_id AND tgt.current_flag = 1
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
    FROM #dedup src
    LEFT JOIN dim.review_cycle tgt
           ON tgt.review_bk = src.review_id AND tgt.current_flag = 1
    LEFT JOIN dim.service svc
           ON svc.service_bk = src.service_id AND svc.current_flag = 1
    WHERE tgt.review_bk IS NULL OR tgt.record_hash <> src.row_hash;
    DROP TABLE IF EXISTS #dedup;
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
    WHERE issue.current_flag = 1
      AND existing.issue_snapshot_sk IS NULL;
END
GO

IF OBJECT_ID('warehouse.usp_backfill_issue_snapshot', 'P') IS NOT NULL
    DROP PROCEDURE warehouse.usp_backfill_issue_snapshot;
GO

CREATE PROCEDURE warehouse.usp_backfill_issue_snapshot
    @StartDate DATE = NULL,
    @EndDate   DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @Start DATE = ISNULL(@StartDate, (SELECT MIN([date]) FROM dim.date));
    DECLARE @End   DATE = ISNULL(@EndDate, CAST(SYSUTCDATETIME() AS DATE));

    ;WITH date_span AS (
        SELECT date_sk, [date]
        FROM dim.date
        WHERE [date] BETWEEN @Start AND @End
    )
    INSERT INTO fact.issue_snapshot (
        snapshot_date_sk, issue_sk, project_sk, client_sk, project_type_sk,
        status, is_open, is_closed, backlog_age_days, resolution_days,
        urgency_score, complexity_score, sentiment_score, comment_count,
        high_priority_flag, record_source
    )
    SELECT
        d.date_sk,
        i.issue_sk,
        i.project_sk,
        p.client_sk,
        p.project_type_sk,
        CASE
            WHEN i.closed_date_sk IS NOT NULL AND i.closed_date_sk <= d.date_sk THEN 'closed'
            ELSE i.status
        END AS status,
        CASE WHEN i.closed_date_sk IS NULL OR i.closed_date_sk > d.date_sk THEN 1 ELSE 0 END AS is_open,
        CASE WHEN i.closed_date_sk IS NOT NULL AND i.closed_date_sk <= d.date_sk THEN 1 ELSE 0 END AS is_closed,
        CASE
            WHEN i.created_date_sk IS NOT NULL
                 AND i.created_date_sk <= d.date_sk
            THEN DATEDIFF(DAY, CAST(CONVERT(VARCHAR(8), i.created_date_sk) AS DATE), d.[date])
            ELSE NULL
        END AS backlog_age_days,
        CASE
            WHEN i.closed_date_sk IS NOT NULL
                 AND i.created_date_sk IS NOT NULL
                 AND i.closed_date_sk <= d.date_sk
            THEN DATEDIFF(DAY, CAST(CONVERT(VARCHAR(8), i.created_date_sk) AS DATE), CAST(CONVERT(VARCHAR(8), i.closed_date_sk) AS DATE))
            ELSE NULL
        END AS resolution_days,
        proc_issue.urgency_score,
        proc_issue.complexity_score,
        proc_issue.sentiment_score,
        proc_issue.comment_count,
        CASE WHEN i.priority IN ('critical', 'high') THEN 1 ELSE 0 END AS high_priority_flag,
        'warehouse.usp_backfill_issue_snapshot' AS record_source
    FROM dim.issue i
    JOIN date_span d
      ON i.created_date_sk IS NULL OR i.created_date_sk <= d.date_sk
    LEFT JOIN dim.project p ON i.project_sk = p.project_sk
    LEFT JOIN stg.processed_issues proc_issue
           ON proc_issue.issue_id = i.issue_bk
          AND proc_issue.source_system = i.source_system
    LEFT JOIN fact.issue_snapshot existing
           ON existing.issue_sk = i.issue_sk
          AND existing.snapshot_date_sk = d.date_sk
    WHERE i.current_flag = 1
      AND (i.created_date_sk IS NULL OR i.created_date_sk <= d.date_sk)
      AND existing.issue_snapshot_sk IS NULL;
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
    WHERE issue.current_flag = 1
      AND issue.closed_date_sk = CONVERT(INT, FORMAT(@Today, 'yyyyMMdd'))
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

    -- Compute issue counts in a ±14 day window around the review's planned date
    IF OBJECT_ID('tempdb..#review_issue_counts') IS NOT NULL DROP TABLE #review_issue_counts;

    ;WITH review_windows AS (
        SELECT
            rc.review_cycle_sk,
            rc.service_sk,
            svc.project_sk,
            rc.planned_date_sk,
            DATEADD(DAY, -14, CAST(CONVERT(VARCHAR(8), rc.planned_date_sk) AS DATE)) AS window_start,
            DATEADD(DAY, 14, CAST(CONVERT(VARCHAR(8), rc.planned_date_sk) AS DATE)) AS window_end
        FROM dim.review_cycle rc
        JOIN dim.service svc ON rc.service_sk = svc.service_sk
        WHERE rc.planned_date_sk IS NOT NULL
    )
    SELECT
        rw.review_cycle_sk,
        COUNT(DISTINCT CASE WHEN i.created_date_sk BETWEEN CONVERT(INT, FORMAT(rw.window_start, 'yyyyMMdd')) 
                                                        AND CONVERT(INT, FORMAT(rw.window_end, 'yyyyMMdd')) 
                            THEN i.issue_sk END) AS issue_count_window,
        COUNT(DISTINCT CASE WHEN i.closed_date_sk BETWEEN CONVERT(INT, FORMAT(rw.window_start, 'yyyyMMdd')) 
                                                       AND CONVERT(INT, FORMAT(rw.window_end, 'yyyyMMdd')) 
                            THEN i.issue_sk END) AS issue_closed_window
    INTO #review_issue_counts
    FROM review_windows rw
    LEFT JOIN dim.issue i ON i.project_sk = rw.project_sk AND i.current_flag = 1
    GROUP BY rw.review_cycle_sk;

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
        ISNULL(ric.issue_count_window, 0),
        ISNULL(ric.issue_closed_window, 0),
        'warehouse.usp_load_fact_review_cycle'
    FROM dim.review_cycle rc
    JOIN dim.service svc ON rc.service_sk = svc.service_sk
    JOIN dim.project proj ON svc.project_sk = proj.project_sk
    LEFT JOIN #review_issue_counts ric ON ric.review_cycle_sk = rc.review_cycle_sk
    WHERE NOT EXISTS (
        SELECT 1
        FROM fact.review_cycle fr
        WHERE fr.review_cycle_sk = rc.review_cycle_sk
    );

    DROP TABLE IF EXISTS #review_issue_counts;
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
    DECLARE @Today DATE = CAST(GETDATE() AS DATE);

    DELETE FROM fact.project_kpi_monthly WHERE month_date_sk = @MonthSk;

    ;WITH resolved_issues AS (
        SELECT
            CONCAT(vi.source, ':', vi.issue_id) AS issue_key,
            COALESCE(p_id.project_sk, palias.project_sk, p_name.project_sk) AS project_sk,
            UPPER(CONVERT(NVARCHAR(50), vi.status)) AS status,
            UPPER(CONVERT(NVARCHAR(50), vi.priority)) AS priority,
            vi.created_at,
            vi.closed_at
        FROM dbo.vw_ProjectManagement_AllIssues vi
        LEFT JOIN dim.project p_id
               ON p_id.project_bk = TRY_CONVERT(
                    INT,
                    CONVERT(NVARCHAR(50), vi.project_id)
               )
              AND p_id.current_flag = 1
        LEFT JOIN dim.project_alias palias
               ON palias.alias_name = vi.project_name
              AND palias.current_flag = 1
        LEFT JOIN dim.project p_name
               ON p_name.project_name = vi.project_name
              AND p_name.current_flag = 1
        WHERE vi.issue_id IS NOT NULL
    ),
    issue_metrics AS (
        SELECT
            ri.project_sk,
            COUNT(DISTINCT ri.issue_key) AS total_issues,
            SUM(CASE WHEN ri.closed_at IS NULL OR CAST(ri.closed_at AS DATE) > @MonthEnd THEN 1 ELSE 0 END) AS open_issues,
            SUM(CASE WHEN ri.closed_at IS NOT NULL AND CAST(ri.closed_at AS DATE) <= @MonthEnd THEN 1 ELSE 0 END) AS closed_issues,
            SUM(CASE WHEN ri.priority IN ('CRITICAL','HIGH','URGENT') THEN 1 ELSE 0 END) AS high_priority_issues,
            AVG(
                CASE 
                    WHEN ri.closed_at IS NOT NULL 
                         AND ri.created_at IS NOT NULL 
                         AND CAST(ri.closed_at AS DATE) >= CAST(ri.created_at AS DATE)
                    THEN CONVERT(DECIMAL(18,4), DATEDIFF(DAY, ri.created_at, ri.closed_at))
                END
            ) AS avg_resolution_days
        FROM resolved_issues ri
        WHERE ri.project_sk IS NOT NULL
          AND (ri.created_at IS NULL OR CAST(ri.created_at AS DATE) <= @MonthEnd)
        GROUP BY ri.project_sk
    ),
    service_status AS (
        SELECT
            p.project_sk,
            SUM(CASE WHEN LOWER(ps.status) = 'in_progress' THEN 1 ELSE 0 END) AS services_in_progress,
            SUM(CASE WHEN LOWER(ps.status) = 'completed' THEN 1 ELSE 0 END) AS services_completed
        FROM dim.project p
        INNER JOIN dbo.ProjectServices ps
            ON ps.project_id = p.project_bk
        WHERE p.current_flag = 1
        GROUP BY p.project_sk
    ),
    review_metrics AS (
        SELECT
            p.project_sk,
            COUNT(sr.review_id) AS total_reviews,
            SUM(CASE WHEN sr.status IN ('completed', 'report_issued', 'closed') THEN 1 ELSE 0 END) AS completed_reviews,
            SUM(
                CASE
                    WHEN sr.status NOT IN ('completed', 'report_issued', 'closed')
                         AND sr.due_date IS NOT NULL
                         AND sr.due_date < @Today
                    THEN 1 ELSE 0
                END
            ) AS overdue_reviews
        FROM dim.project p
        INNER JOIN dbo.ProjectServices ps
            ON ps.project_id = p.project_bk
        INNER JOIN dbo.ServiceReviews sr
            ON sr.service_id = ps.service_id
        WHERE p.current_flag = 1
        GROUP BY p.project_sk
    )
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
        ISNULL(im.total_issues, 0) AS total_issues,
        ISNULL(im.open_issues, 0) AS open_issues,
        ISNULL(im.closed_issues, 0) AS closed_issues,
        ISNULL(im.high_priority_issues, 0) AS high_priority_issues,
        CAST(im.avg_resolution_days AS DECIMAL(9,2)) AS avg_resolution_days,
        MAX(ISNULL(rm.total_reviews, 0)) AS review_count,
        MAX(ISNULL(rm.completed_reviews, 0)) AS completed_reviews,
        MAX(ISNULL(rm.overdue_reviews, 0)) AS overdue_reviews,
        MAX(ISNULL(ss.services_in_progress, 0)) AS services_in_progress,
        MAX(ISNULL(ss.services_completed, 0)) AS services_completed,
        SUM(ISNULL(service_month.earned_value, 0)) AS earned_value,
        SUM(ISNULL(service_month.claimed_to_date, 0)) AS claimed_to_date,
        SUM(ISNULL(service_month.variance_fee, 0)) AS variance_fee,
        'warehouse.usp_load_fact_project_kpi_monthly'
    FROM dim.project proj
    LEFT JOIN issue_metrics im ON im.project_sk = proj.project_sk
    LEFT JOIN service_status ss ON ss.project_sk = proj.project_sk
    LEFT JOIN review_metrics rm ON rm.project_sk = proj.project_sk
    LEFT JOIN fact.service_monthly service_month
           ON service_month.project_sk = proj.project_sk
          AND service_month.month_date_sk = @MonthSk
    WHERE proj.current_flag = 1
    GROUP BY proj.project_sk, proj.client_sk, proj.project_type_sk, im.total_issues, im.open_issues,
             im.closed_issues, im.high_priority_issues, im.avg_resolution_days;
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

    -- Review-Issue bridge: link issues created/closed in the review window
    INSERT INTO brg.review_issue (review_cycle_sk, issue_sk, relationship_type)
    SELECT DISTINCT
        rw.review_cycle_sk,
        i.issue_sk,
        CASE
            WHEN i.created_date_sk BETWEEN CONVERT(INT, FORMAT(rw.window_start, 'yyyyMMdd'))
                                       AND CONVERT(INT, FORMAT(rw.window_end, 'yyyyMMdd'))
                 AND i.closed_date_sk BETWEEN CONVERT(INT, FORMAT(rw.window_start, 'yyyyMMdd'))
                                          AND CONVERT(INT, FORMAT(rw.window_end, 'yyyyMMdd'))
            THEN 'opened_and_closed_during'
            WHEN i.created_date_sk BETWEEN CONVERT(INT, FORMAT(rw.window_start, 'yyyyMMdd'))
                                       AND CONVERT(INT, FORMAT(rw.window_end, 'yyyyMMdd'))
            THEN 'opened_during'
            WHEN i.closed_date_sk BETWEEN CONVERT(INT, FORMAT(rw.window_start, 'yyyyMMdd'))
                                      AND CONVERT(INT, FORMAT(rw.window_end, 'yyyyMMdd'))
            THEN 'closed_during'
            ELSE 'active_during'
        END
    FROM (
        SELECT
            rc.review_cycle_sk,
            svc.project_sk,
            DATEADD(DAY, -14, CAST(CONVERT(VARCHAR(8), rc.planned_date_sk) AS DATE)) AS window_start,
            DATEADD(DAY, 14, CAST(CONVERT(VARCHAR(8), rc.planned_date_sk) AS DATE)) AS window_end
        FROM dim.review_cycle rc
        JOIN dim.service svc ON rc.service_sk = svc.service_sk
        WHERE rc.planned_date_sk IS NOT NULL
    ) rw
    JOIN dim.issue i ON i.project_sk = rw.project_sk AND i.current_flag = 1
    WHERE (
        i.created_date_sk BETWEEN CONVERT(INT, FORMAT(rw.window_start, 'yyyyMMdd'))
                              AND CONVERT(INT, FORMAT(rw.window_end, 'yyyyMMdd'))
        OR i.closed_date_sk BETWEEN CONVERT(INT, FORMAT(rw.window_start, 'yyyyMMdd'))
                                AND CONVERT(INT, FORMAT(rw.window_end, 'yyyyMMdd'))
    )
    AND NOT EXISTS (
        SELECT 1
        FROM brg.review_issue bri
        WHERE bri.review_cycle_sk = rw.review_cycle_sk
          AND bri.issue_sk = i.issue_sk
    );
END
GO
