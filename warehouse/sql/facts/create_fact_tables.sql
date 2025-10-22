/*
    Warehouse Fact Tables
    - Issue and review/service metrics aligned with dimensional model.
*/

USE [ProjectManagement];
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'fact')
BEGIN
    EXEC('CREATE SCHEMA fact AUTHORIZATION dbo;');
END
GO

/* ISSUE SNAPSHOT FACT (daily grain) */
IF OBJECT_ID('fact.issue_snapshot', 'U') IS NULL
BEGIN
    CREATE TABLE fact.issue_snapshot (
        issue_snapshot_sk BIGINT        NOT NULL IDENTITY(1,1) PRIMARY KEY,
        snapshot_date_sk  INT           NOT NULL,
        issue_sk          INT           NOT NULL,
        project_sk        INT           NULL,
        client_sk         INT           NULL,
        project_type_sk   INT           NULL,
        status            NVARCHAR(50)  NOT NULL,
        is_open           BIT           NOT NULL,
        is_closed         BIT           NOT NULL,
        backlog_age_days  INT           NULL,
        resolution_days   INT           NULL,
        urgency_score     DECIMAL(4,2)  NULL,
        complexity_score  DECIMAL(4,2)  NULL,
        sentiment_score   DECIMAL(4,2)  NULL,
        comment_count     INT           NULL,
        high_priority_flag BIT          NULL,
        record_source     NVARCHAR(50)  NOT NULL,
        load_ts           DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME()
    );
    CREATE INDEX ix_issue_snapshot_date ON fact.issue_snapshot(snapshot_date_sk);
    CREATE INDEX ix_issue_snapshot_issue ON fact.issue_snapshot(issue_sk, snapshot_date_sk);
END
GO

/* ISSUE ACTIVITY FACT (event grain) */
IF OBJECT_ID('fact.issue_activity', 'U') IS NULL
BEGIN
    CREATE TABLE fact.issue_activity (
        issue_activity_sk BIGINT        NOT NULL IDENTITY(1,1) PRIMARY KEY,
        issue_sk          INT           NOT NULL,
        event_type        NVARCHAR(50)  NOT NULL, -- created, status_change, closed, reopened
        event_date_sk     INT           NOT NULL,
        event_ts          DATETIME2     NOT NULL,
        status_from       NVARCHAR(50)  NULL,
        status_to         NVARCHAR(50)  NULL,
        project_sk        INT           NULL,
        service_sk        INT           NULL,
        review_cycle_sk   INT           NULL,
        resolution_days   INT           NULL,
        backlog_age_days  INT           NULL,
        comment_count     INT           NULL,
        record_source     NVARCHAR(50)  NOT NULL,
        load_ts           DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME()
    );
    CREATE INDEX ix_issue_activity_issue ON fact.issue_activity(issue_sk, event_ts);
END
GO

/* SERVICE FACT (monthly snapshot) */
IF OBJECT_ID('fact.service_monthly', 'U') IS NULL
BEGIN
    CREATE TABLE fact.service_monthly (
        service_monthly_sk BIGINT        NOT NULL IDENTITY(1,1) PRIMARY KEY,
        service_sk         INT           NOT NULL,
        project_sk         INT           NOT NULL,
        client_sk          INT           NULL,
        project_type_sk    INT           NULL,
        month_date_sk      INT           NOT NULL,
        planned_quantity   DECIMAL(18,4) NULL,
        actual_quantity    DECIMAL(18,4) NULL,
        planned_fee        DECIMAL(18,2) NULL,
        earned_value       DECIMAL(18,2) NULL,
        claimed_to_date    DECIMAL(18,2) NULL,
        variance_fee       DECIMAL(18,2) NULL,
        progress_pct       DECIMAL(9,4)  NULL,
        status             NVARCHAR(50)  NULL,
        review_count       INT           NULL,
        completed_reviews  INT           NULL,
        overdue_reviews    INT           NULL,
        record_source      NVARCHAR(50)  NOT NULL,
        load_ts            DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME()
    );
    CREATE INDEX ix_service_monthly_month ON fact.service_monthly(month_date_sk);
    CREATE INDEX ix_service_monthly_service ON fact.service_monthly(service_sk, month_date_sk);
END
GO

/* REVIEW CYCLE FACT */
IF OBJECT_ID('fact.review_cycle', 'U') IS NULL
BEGIN
    CREATE TABLE fact.review_cycle (
        review_cycle_fact_sk BIGINT       NOT NULL IDENTITY(1,1) PRIMARY KEY,
        review_cycle_sk      INT          NOT NULL,
        service_sk           INT          NOT NULL,
        project_sk           INT          NOT NULL,
        client_sk            INT          NULL,
        project_type_sk      INT          NULL,
        planned_date_sk      INT          NULL,
        due_date_sk          INT          NULL,
        actual_date_sk       INT          NULL,
        planned_vs_actual_days INT        NULL,
        is_completed         BIT          NULL,
        is_overdue           BIT          NULL,
        status               NVARCHAR(30) NULL,
        weight_factor        DECIMAL(9,4) NULL,
        issue_count_window   INT          NULL, -- Issues created within review window
        issue_closed_window  INT          NULL, -- Issues closed post-review
        record_source        NVARCHAR(50) NOT NULL,
        load_ts              DATETIME2    NOT NULL DEFAULT SYSUTCDATETIME()
    );
    CREATE INDEX ix_review_cycle_dates ON fact.review_cycle(planned_date_sk, actual_date_sk);
END
GO

/* REVIEW EVENT FACT */
IF OBJECT_ID('fact.review_event', 'U') IS NULL
BEGIN
    CREATE TABLE fact.review_event (
        review_event_sk   BIGINT        NOT NULL IDENTITY(1,1) PRIMARY KEY,
        review_cycle_sk   INT           NOT NULL,
        event_type        NVARCHAR(50)  NOT NULL,
        event_date_sk     INT           NOT NULL,
        event_ts          DATETIME2     NOT NULL,
        status_from       NVARCHAR(30)  NULL,
        status_to         NVARCHAR(30)  NULL,
        project_sk        INT           NULL,
        service_sk        INT           NULL,
        record_source     NVARCHAR(50)  NOT NULL,
        load_ts           DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME()
    );
    CREATE INDEX ix_review_event_cycle ON fact.review_event(review_cycle_sk, event_ts);
END
GO

/* PROJECT KPI FACT (monthly aggregate) */
IF OBJECT_ID('fact.project_kpi_monthly', 'U') IS NULL
BEGIN
    CREATE TABLE fact.project_kpi_monthly (
        project_kpi_sk     BIGINT        NOT NULL IDENTITY(1,1) PRIMARY KEY,
        project_sk         INT           NOT NULL,
        client_sk          INT           NULL,
        project_type_sk    INT           NULL,
        month_date_sk      INT           NOT NULL,
        total_issues       INT           NULL,
        open_issues        INT           NULL,
        closed_issues      INT           NULL,
        high_priority_issues INT         NULL,
        avg_resolution_days DECIMAL(9,2) NULL,
        review_count       INT           NULL,
        completed_reviews  INT           NULL,
        overdue_reviews    INT           NULL,
        services_in_progress INT         NULL,
        services_completed INT           NULL,
        earned_value       DECIMAL(18,2) NULL,
        claimed_to_date    DECIMAL(18,2) NULL,
        variance_fee       DECIMAL(18,2) NULL,
        record_source      NVARCHAR(50)  NOT NULL,
        load_ts            DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME()
    );
    CREATE INDEX ix_project_kpi_month ON fact.project_kpi_monthly(month_date_sk, project_sk);
END
GO
