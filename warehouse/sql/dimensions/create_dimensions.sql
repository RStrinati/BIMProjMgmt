/*
    Warehouse Dimension Tables (Star Schema)
    Implements surrogate keys, type-2 support where required.
*/

USE [ProjectManagement];
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'dim')
BEGIN
    EXEC('CREATE SCHEMA dim AUTHORIZATION dbo;');
END
GO

/* DATE DIMENSION */
IF OBJECT_ID('dim.date', 'U') IS NULL
BEGIN
    CREATE TABLE dim.date (
        date_sk             INT           NOT NULL PRIMARY KEY, -- YYYYMMDD
        [date]              DATE          NOT NULL,
        day_number_of_week  TINYINT       NOT NULL,
        day_name            NVARCHAR(20)  NOT NULL,
        day_of_month        TINYINT       NOT NULL,
        day_of_year         SMALLINT      NOT NULL,
        week_of_year        TINYINT       NOT NULL,
        iso_week_of_year    TINYINT       NOT NULL,
        week_start_date     DATE          NOT NULL,
        month_number        TINYINT       NOT NULL,
        month_name          NVARCHAR(20)  NOT NULL,
        quarter_number      TINYINT       NOT NULL,
        year_number         SMALLINT      NOT NULL,
        fiscal_month_number TINYINT       NULL,
        fiscal_quarter      TINYINT       NULL,
        fiscal_year         SMALLINT      NULL,
        is_weekend          BIT           NOT NULL,
        is_holiday          BIT           NOT NULL DEFAULT 0
    );
END
GO

/* PROJECT DIMENSION */
IF OBJECT_ID('dim.project', 'U') IS NULL
BEGIN
    CREATE TABLE dim.project (
        project_sk        INT           NOT NULL IDENTITY(1,1) PRIMARY KEY,
        project_bk        INT           NOT NULL, -- business key
        project_name      NVARCHAR(510) NOT NULL,
        client_sk         INT           NULL,
        project_type_sk   INT           NULL,
        status            NVARCHAR(100) NULL,
        priority          NVARCHAR(100) NULL,
        start_date        DATE          NULL,
        end_date          DATE          NULL,
        area_hectares     DECIMAL(18,4) NULL,
        city              NVARCHAR(255) NULL,
        state             NVARCHAR(255) NULL,
        country           NVARCHAR(255) NULL,
        created_at        DATETIME2     NULL,
        updated_at        DATETIME2     NULL,
        current_flag      BIT           NOT NULL DEFAULT 1,
        effective_start   DATETIME2     NOT NULL,
        effective_end     DATETIME2     NULL,
        record_hash       BINARY(32)    NULL,
        record_source     NVARCHAR(50)  NOT NULL
    );
    CREATE UNIQUE INDEX uq_dim_project_current ON dim.project(project_bk) WHERE current_flag = 1;
END
GO

/* CLIENT DIMENSION */
IF OBJECT_ID('dim.client', 'U') IS NULL
BEGIN
    CREATE TABLE dim.client (
        client_sk       INT           NOT NULL IDENTITY(1,1) PRIMARY KEY,
        client_bk       INT           NOT NULL,
        client_name     NVARCHAR(255) NOT NULL,
        contact_name    NVARCHAR(255) NULL,
        contact_email   NVARCHAR(255) NULL,
        industry_sector NVARCHAR(255) NULL,
        country         NVARCHAR(255) NULL,
        current_flag    BIT           NOT NULL DEFAULT 1,
        effective_start DATETIME2     NOT NULL,
        effective_end   DATETIME2     NULL,
        record_hash     BINARY(32)    NULL,
        record_source   NVARCHAR(50)  NOT NULL
    );
    CREATE UNIQUE INDEX uq_dim_client_current ON dim.client(client_bk) WHERE current_flag = 1;
END
GO

/* PROJECT TYPE DIMENSION */
IF OBJECT_ID('dim.project_type', 'U') IS NULL
BEGIN
    CREATE TABLE dim.project_type (
        project_type_sk   INT           NOT NULL IDENTITY(1,1) PRIMARY KEY,
        project_type_bk   INT           NOT NULL,
        project_type_name NVARCHAR(255) NOT NULL,
        category          NVARCHAR(255) NULL,
        current_flag      BIT           NOT NULL DEFAULT 1,
        effective_start   DATETIME2     NOT NULL,
        effective_end     DATETIME2     NULL,
        record_hash       BINARY(32)    NULL,
        record_source     NVARCHAR(50)  NOT NULL
    );
    CREATE UNIQUE INDEX uq_dim_project_type_current ON dim.project_type(project_type_bk) WHERE current_flag = 1;
END
GO

/* ISSUE CATEGORY DIMENSION */
IF OBJECT_ID('dim.issue_category', 'U') IS NULL
BEGIN
    CREATE TABLE dim.issue_category (
        issue_category_sk   INT           NOT NULL IDENTITY(1,1) PRIMARY KEY,
        category_bk         INT           NOT NULL,
        category_name       NVARCHAR(100) NOT NULL,
        parent_category_sk  INT           NULL,
        category_level      INT           NOT NULL,
        description         NVARCHAR(500) NULL,
        lineage_path        NVARCHAR(500) NULL,
        level1_name         NVARCHAR(100) NULL,
        level2_name         NVARCHAR(100) NULL,
        level3_name         NVARCHAR(100) NULL,
        current_flag        BIT           NOT NULL DEFAULT 1,
        effective_start     DATETIME2     NOT NULL,
        effective_end       DATETIME2     NULL,
        record_hash         BINARY(32)    NULL,
        record_source       NVARCHAR(50)  NOT NULL
    );
    CREATE UNIQUE INDEX uq_dim_issue_category_current ON dim.issue_category(category_bk) WHERE current_flag = 1;
END
GO

/* ISSUE DIMENSION (TYPE-2) */
IF OBJECT_ID('dim.issue', 'U') IS NULL
BEGIN
    CREATE TABLE dim.issue (
        issue_sk                INT            NOT NULL IDENTITY(1,1) PRIMARY KEY,
        issue_bk                NVARCHAR(255)  NOT NULL,
        source_system           NVARCHAR(32)   NOT NULL,
        project_sk              INT            NULL,
        title                   NVARCHAR(500)  NULL,
        status                  NVARCHAR(50)   NULL,
        priority                NVARCHAR(50)   NULL,
        priority_normalized     NVARCHAR(50)   NULL,
        assignee_sk             INT            NULL,
        author_sk               INT            NULL,
        created_date_sk         INT            NULL,
        closed_date_sk          INT            NULL,
        discipline_category_sk  INT            NULL,
        primary_category_sk     INT            NULL,
        secondary_category_sk   INT            NULL,
        location_raw            NVARCHAR(255)  NULL,
        location_root           NVARCHAR(255)  NULL,
        location_building       NVARCHAR(255)  NULL,
        location_level          NVARCHAR(255)  NULL,
        current_flag            BIT            NOT NULL DEFAULT 1,
        effective_start         DATETIME2      NOT NULL,
        effective_end           DATETIME2      NULL,
        record_hash             BINARY(32)     NULL,
        record_source           NVARCHAR(50)   NOT NULL
    );
    CREATE UNIQUE INDEX uq_dim_issue_current ON dim.issue(issue_bk, source_system) WHERE current_flag = 1;
END
GO

/* USER DIMENSION */
IF OBJECT_ID('dim.[user]', 'U') IS NULL
BEGIN
    CREATE TABLE dim.[user] (
        user_sk        INT           NOT NULL IDENTITY(1,1) PRIMARY KEY,
        user_bk        NVARCHAR(255) NOT NULL,
        display_name   NVARCHAR(255) NULL,
        email          NVARCHAR(255) NULL,
        source_system  NVARCHAR(32)  NOT NULL,
        role           NVARCHAR(100) NULL,
        current_flag   BIT           NOT NULL DEFAULT 1,
        effective_start DATETIME2    NOT NULL,
        effective_end   DATETIME2    NULL,
        record_hash     BINARY(32)   NULL,
        record_source   NVARCHAR(50) NOT NULL
    );
    CREATE UNIQUE INDEX uq_dim_user_current ON dim.[user](user_bk, source_system) WHERE current_flag = 1;
END
GO

/* SERVICE DIMENSION */
IF OBJECT_ID('dim.service', 'U') IS NULL
BEGIN
    CREATE TABLE dim.service (
        service_sk       INT           NOT NULL IDENTITY(1,1) PRIMARY KEY,
        service_bk       INT           NOT NULL,
        project_sk       INT           NOT NULL,
        service_code     NVARCHAR(100) NULL,
        service_name     NVARCHAR(255) NOT NULL,
        phase            NVARCHAR(255) NULL,
        unit_type        NVARCHAR(100) NULL,
        unit_qty         DECIMAL(18,4) NULL,
        unit_rate        DECIMAL(18,4) NULL,
        lump_sum_fee     DECIMAL(18,2) NULL,
        agreed_fee       DECIMAL(18,2) NULL,
        progress_pct     DECIMAL(9,4)  NULL,
        status           NVARCHAR(50)  NULL,
        current_flag     BIT           NOT NULL DEFAULT 1,
        effective_start  DATETIME2     NOT NULL,
        effective_end    DATETIME2     NULL,
        record_hash      BINARY(32)    NULL,
        record_source    NVARCHAR(50)  NOT NULL
    );
    CREATE UNIQUE INDEX uq_dim_service_current ON dim.service(service_bk) WHERE current_flag = 1;
END
GO

/* REVIEW CYCLE DIMENSION */
IF OBJECT_ID('dim.review_cycle', 'U') IS NULL
BEGIN
    CREATE TABLE dim.review_cycle (
        review_cycle_sk  INT           NOT NULL IDENTITY(1,1) PRIMARY KEY,
        review_bk        INT           NOT NULL,
        service_sk       INT           NOT NULL,
        project_sk       INT           NOT NULL,
        cycle_no         INT           NOT NULL,
        planned_date_sk  INT           NULL,
        due_date_sk      INT           NULL,
        stage_sk         INT           NULL,
        weight_factor    DECIMAL(9,4)  NULL,
        status           NVARCHAR(30)  NULL,
        current_flag     BIT           NOT NULL DEFAULT 1,
        effective_start  DATETIME2     NOT NULL,
        effective_end    DATETIME2     NULL,
        record_hash      BINARY(32)    NULL,
        record_source    NVARCHAR(50)  NOT NULL
    );
    CREATE UNIQUE INDEX uq_dim_review_cycle_current ON dim.review_cycle(review_bk) WHERE current_flag = 1;
END
GO

/* REVIEW STAGE DIMENSION */
IF OBJECT_ID('dim.review_stage', 'U') IS NULL
BEGIN
    CREATE TABLE dim.review_stage (
        stage_sk        INT           NOT NULL IDENTITY(1,1) PRIMARY KEY,
        stage_bk        INT           NOT NULL,
        stage_name      NVARCHAR(255) NOT NULL,
        start_date_sk   INT           NULL,
        end_date_sk     INT           NULL,
        number_of_reviews INT         NULL,
        current_flag    BIT           NOT NULL DEFAULT 1,
        effective_start DATETIME2     NOT NULL,
        effective_end   DATETIME2     NULL,
        record_hash     BINARY(32)    NULL,
        record_source   NVARCHAR(50)  NOT NULL
    );
    CREATE UNIQUE INDEX uq_dim_review_stage_current ON dim.review_stage(stage_bk) WHERE current_flag = 1;
END
GO

/* PROJECT ALIAS DIMENSION */
IF OBJECT_ID('dim.project_alias', 'U') IS NULL
BEGIN
    CREATE TABLE dim.project_alias (
        project_alias_sk INT IDENTITY(1,1) PRIMARY KEY,
        pm_project_id    INT           NOT NULL,
        alias_name       NVARCHAR(510) NOT NULL,
        alias_type       NVARCHAR(100) NULL,
        project_sk       INT           NOT NULL,
        current_flag     BIT           NOT NULL DEFAULT 1,
        effective_start  DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
        effective_end    DATETIME2     NULL,
        record_hash      BINARY(32)    NULL,
        record_source    NVARCHAR(50)  NOT NULL,
        CONSTRAINT fk_dim_project_alias_project
            FOREIGN KEY (project_sk) REFERENCES dim.project(project_sk)
    );

    CREATE UNIQUE INDEX ux_project_alias_current
        ON dim.project_alias(pm_project_id, alias_name, current_flag)
        WHERE current_flag = 1;
END
GO
