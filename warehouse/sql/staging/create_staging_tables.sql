/*
    Warehouse Staging Layer
    - Stores raw snapshots from source systems prior to transformation.
    - Tables keep close parity with source schema plus ingestion metadata.
*/

USE [ProjectManagement];
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'stg')
BEGIN
    EXEC('CREATE SCHEMA stg AUTHORIZATION dbo;');
END
GO

/* ISSUES (ACC + Revizto unified view) */
IF OBJECT_ID('stg.issues', 'U') IS NULL
BEGIN
    CREATE TABLE stg.issues (
        source_system        NVARCHAR(32)  NOT NULL, -- ACC / Revizto
        issue_id             NVARCHAR(255) NOT NULL,
        project_name         NVARCHAR(510) NULL,
        project_id_raw       NVARCHAR(255) NULL,
        status               NVARCHAR(50)  NULL,
        priority             NVARCHAR(50)  NULL,
        priority_normalized  NVARCHAR(50)  NULL,
        title                NVARCHAR(500) NULL,
        description          NVARCHAR(MAX) NULL,
        assignee             NVARCHAR(255) NULL,
        author               NVARCHAR(255) NULL,
        created_at           DATETIME2     NULL,
        closed_at            DATETIME2     NULL,
        last_activity_date   DATETIME2     NULL,
        due_date             DATETIME2     NULL,
        discipline           NVARCHAR(100) NULL,
        category_primary     NVARCHAR(100) NULL,
        category_secondary   NVARCHAR(100) NULL,
        location_raw         NVARCHAR(255) NULL,
        location_root        NVARCHAR(255) NULL,
        location_building    NVARCHAR(255) NULL,
        location_level       NVARCHAR(255) NULL,
        source_load_ts       DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
        record_hash          BINARY(32)    NULL,
        record_source        NVARCHAR(50)  NOT NULL,
        CONSTRAINT pk_stg_issues PRIMARY KEY (source_system, issue_id, source_load_ts)
    );
END
GO

/* PROCESSED ISSUE ANALYTICS */
IF OBJECT_ID('stg.processed_issues', 'U') IS NULL
BEGIN
    CREATE TABLE stg.processed_issues (
        source_system            NVARCHAR(32)  NOT NULL,
        issue_id                 NVARCHAR(255) NOT NULL,
        project_id               INT           NULL,
        urgency_score            DECIMAL(4,2)  NULL,
        complexity_score         DECIMAL(4,2)  NULL,
        sentiment_score          DECIMAL(4,2)  NULL,
        categorization_confidence DECIMAL(4,2) NULL,
        discipline_category_id   INT           NULL,
        primary_category_id      INT           NULL,
        secondary_category_id    INT           NULL,
        resolution_days          INT           NULL,
        is_recurring             BIT           NULL,
        recurring_cluster_id     INT           NULL,
        comment_count            INT           NULL,
        processed_at             DATETIME2     NULL,
        processing_version       NVARCHAR(100) NULL,
        extracted_keywords_json  NVARCHAR(MAX) NULL,
        record_source            NVARCHAR(50)  NOT NULL,
        source_load_ts           DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
        record_hash              BINARY(32)    NULL,
        CONSTRAINT pk_stg_processed_issues PRIMARY KEY (source_system, issue_id, source_load_ts)
    );
END
GO

/* PROJECT MASTER DATA */
IF OBJECT_ID('stg.projects', 'U') IS NULL
BEGIN
    CREATE TABLE stg.projects (
        project_id           INT           NOT NULL,
        project_name         NVARCHAR(510) NOT NULL,
        client_id            INT           NULL,
        project_type_id      INT           NULL,
        status               NVARCHAR(100) NULL,
        priority             NVARCHAR(100) NULL,
        start_date           DATE          NULL,
        end_date             DATE          NULL,
        area_hectares        DECIMAL(18,4) NULL,
        city                 NVARCHAR(255) NULL,
        state                NVARCHAR(255) NULL,
        country              NVARCHAR(255) NULL,
        created_at           DATETIME2     NULL,
        updated_at           DATETIME2     NULL,
        record_source        NVARCHAR(50)  NOT NULL,
        source_load_ts       DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
        record_hash          BINARY(32)    NULL,
        CONSTRAINT pk_stg_projects PRIMARY KEY (project_id, source_load_ts)
    );
END
GO

/* CLIENT LOOKUP */
IF OBJECT_ID('stg.clients', 'U') IS NULL
BEGIN
    CREATE TABLE stg.clients (
        client_id       INT            NOT NULL,
        client_name     NVARCHAR(255)  NOT NULL,
        contact_name    NVARCHAR(255)  NULL,
        contact_email   NVARCHAR(255)  NULL,
        industry_sector NVARCHAR(255)  NULL,
        country         NVARCHAR(255)  NULL,
        record_source   NVARCHAR(50)   NOT NULL,
        source_load_ts  DATETIME2      NOT NULL DEFAULT SYSUTCDATETIME(),
        record_hash     BINARY(32)     NULL,
        CONSTRAINT pk_stg_clients PRIMARY KEY (client_id, source_load_ts)
    );
END
GO

/* PROJECT TYPES */
IF OBJECT_ID('stg.project_types', 'U') IS NULL
BEGIN
    CREATE TABLE stg.project_types (
        project_type_id   INT           NOT NULL,
        project_type_name NVARCHAR(255) NOT NULL,
        category          NVARCHAR(255) NULL,
        record_source     NVARCHAR(50)  NOT NULL,
        source_load_ts    DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
        record_hash       BINARY(32)    NULL,
        CONSTRAINT pk_stg_project_types PRIMARY KEY (project_type_id, source_load_ts)
    );
END
GO

/* SERVICES */
IF OBJECT_ID('stg.project_services', 'U') IS NULL
BEGIN
    CREATE TABLE stg.project_services (
        service_id        INT            NOT NULL,
        project_id        INT            NOT NULL,
        service_code      NVARCHAR(100)  NULL,
        service_name      NVARCHAR(255)  NOT NULL,
        phase             NVARCHAR(255)  NULL,
        unit_type         NVARCHAR(100)  NULL,
        unit_qty          DECIMAL(18,4)  NULL,
        unit_rate         DECIMAL(18,4)  NULL,
        lump_sum_fee      DECIMAL(18,2)  NULL,
        agreed_fee        DECIMAL(18,2)  NULL,
        progress_pct      DECIMAL(9,4)   NULL,
        claimed_to_date   DECIMAL(18,2)  NULL,
        status            NVARCHAR(50)   NULL,
        created_at        DATETIME2      NULL,
        updated_at        DATETIME2      NULL,
        record_source     NVARCHAR(50)   NOT NULL,
        source_load_ts    DATETIME2      NOT NULL DEFAULT SYSUTCDATETIME(),
        record_hash       BINARY(32)     NULL,
        CONSTRAINT pk_stg_project_services PRIMARY KEY (service_id, source_load_ts)
    );
END
GO

/* SERVICE REVIEWS */
IF OBJECT_ID('stg.service_reviews', 'U') IS NULL
BEGIN
    CREATE TABLE stg.service_reviews (
        review_id       INT            NOT NULL,
        service_id      INT            NOT NULL,
        cycle_no        INT            NOT NULL,
        planned_date    DATE           NOT NULL,
        due_date        DATE           NULL,
        actual_date     DATE           NULL,
        status          NVARCHAR(30)   NOT NULL,
        disciplines     NVARCHAR(200)  NULL,
        deliverables    NVARCHAR(200)  NULL,
        weight_factor   DECIMAL(9,4)   NULL,
        evidence_links  NVARCHAR(MAX)  NULL,
        last_status_at  DATETIME2      NULL,
        record_source   NVARCHAR(50)   NOT NULL,
        source_load_ts  DATETIME2      NOT NULL DEFAULT SYSUTCDATETIME(),
        record_hash     BINARY(32)     NULL,
        CONSTRAINT pk_stg_service_reviews PRIMARY KEY (review_id, source_load_ts)
    );
END
GO

/* REVIEW SCHEDULE EVENTS */
IF OBJECT_ID('stg.review_schedule_events', 'U') IS NULL
BEGIN
    CREATE TABLE stg.review_schedule_events (
        event_id         BIGINT        NOT NULL IDENTITY(1,1),
        service_id       INT           NOT NULL,
        review_id        INT           NULL,
        event_type       NVARCHAR(50)  NOT NULL, -- status_change, date_update, completion
        event_ts         DATETIME2     NOT NULL,
        status_from      NVARCHAR(30)  NULL,
        status_to        NVARCHAR(30)  NULL,
        planned_date     DATE          NULL,
        due_date         DATE          NULL,
        actual_date      DATE          NULL,
        record_source    NVARCHAR(50)  NOT NULL,
        source_load_ts   DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT pk_stg_review_schedule_events PRIMARY KEY (event_id)
    );
END
GO

/* PROJECT ALIASES */
IF OBJECT_ID('stg.project_aliases', 'U') IS NULL
BEGIN
    CREATE TABLE stg.project_aliases (
        pm_project_id    INT           NOT NULL,
        alias_name       NVARCHAR(510) NOT NULL,
        alias_type       NVARCHAR(100) NULL, -- optional classifier (name, code, legacy_id, etc.)
        record_source    NVARCHAR(50)  NOT NULL,
        source_load_ts   DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
        record_hash      BINARY(32)    NULL,
        CONSTRAINT pk_stg_project_aliases PRIMARY KEY (pm_project_id, alias_name, source_load_ts)
    );
END
GO

/* ISSUE CATEGORY LOOKUP */
IF OBJECT_ID('stg.issue_categories', 'U') IS NULL
BEGIN
    CREATE TABLE stg.issue_categories (
        category_id        INT            NOT NULL,
        category_name      NVARCHAR(100)  NOT NULL,
        parent_category_id INT            NULL,
        category_level     INT            NOT NULL,
        description        NVARCHAR(500)  NULL,
        record_source      NVARCHAR(50)   NOT NULL,
        source_load_ts     DATETIME2      NOT NULL DEFAULT SYSUTCDATETIME(),
        record_hash        BINARY(32)     NULL,
        CONSTRAINT pk_stg_issue_categories PRIMARY KEY (category_id, source_load_ts)
    );
END
GO
