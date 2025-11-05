/*
    Analytic Marts / Views for BI consumption.
*/

USE [ProjectManagement];
GO

/* Ensure mart schema exists */
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'mart')
BEGIN
    EXEC('CREATE SCHEMA mart AUTHORIZATION dbo;');
END
GO

/* PROJECT OVERVIEW MART */
IF OBJECT_ID('mart.v_project_overview', 'V') IS NOT NULL
    DROP VIEW mart.v_project_overview;
GO

CREATE VIEW mart.v_project_overview
AS
SELECT
    p.project_sk,
    p.project_name,
    c.client_name,
    pt.project_type_name,
    k.month_date_sk,
    d.year_number,
    d.month_number,
    ISNULL(k.total_issues, 0) AS total_issues,
    ISNULL(k.open_issues, 0) AS open_issues,
    ISNULL(k.closed_issues, 0) AS closed_issues,
    ISNULL(k.high_priority_issues, 0) AS high_priority_issues,
    k.avg_resolution_days,
    ISNULL(k.review_count, 0) AS review_count,
    ISNULL(k.completed_reviews, 0) AS completed_reviews,
    ISNULL(k.overdue_reviews, 0) AS overdue_reviews,
    ISNULL(k.services_in_progress, 0) AS services_in_progress,
    ISNULL(k.services_completed, 0) AS services_completed,
    ISNULL(k.earned_value, 0) AS earned_value,
    ISNULL(k.claimed_to_date, 0) AS claimed_to_date,
    ISNULL(k.variance_fee, 0) AS variance_fee
FROM dim.project p
LEFT JOIN fact.project_kpi_monthly k ON k.project_sk = p.project_sk
LEFT JOIN dim.client c ON p.client_sk = c.client_sk
LEFT JOIN dim.project_type pt ON p.project_type_sk = pt.project_type_sk
LEFT JOIN dim.date d ON k.month_date_sk = d.date_sk
WHERE p.current_flag = 1;
GO

/* ISSUE TREND MART */
IF OBJECT_ID('mart.v_issue_trends', 'V') IS NOT NULL
    DROP VIEW mart.v_issue_trends;
GO

CREATE VIEW mart.v_issue_trends
AS
SELECT
    s.snapshot_date_sk,
    d.[date] AS snapshot_date,
    p.project_name,
    c.client_name,
    pt.project_type_name,
    ic.level1_name AS discipline,
    ic.level2_name AS primary_category,
    SUM(CASE WHEN s.is_open = 1 THEN 1 ELSE 0 END) AS open_issues,
    SUM(CASE WHEN s.is_closed = 1 THEN 1 ELSE 0 END) AS closed_issues,
    AVG(s.backlog_age_days) AS avg_backlog_days,
    AVG(s.resolution_days) AS avg_resolution_days,
    AVG(s.urgency_score) AS avg_urgency,
    AVG(s.sentiment_score) AS avg_sentiment
FROM fact.issue_snapshot s
JOIN dim.date d ON s.snapshot_date_sk = d.date_sk
JOIN dim.issue i ON s.issue_sk = i.issue_sk
LEFT JOIN dim.project p ON s.project_sk = p.project_sk
LEFT JOIN dim.client c ON s.client_sk = c.client_sk
LEFT JOIN dim.project_type pt ON s.project_type_sk = pt.project_type_sk
LEFT JOIN brg.issue_category bic ON s.issue_sk = bic.issue_sk AND bic.category_role = 'discipline'
LEFT JOIN dim.issue_category ic ON bic.issue_category_sk = ic.issue_category_sk
GROUP BY s.snapshot_date_sk, d.[date], p.project_name, c.client_name, pt.project_type_name, ic.level1_name, ic.level2_name;
GO

/* REVIEW PERFORMANCE MART */
IF OBJECT_ID('mart.v_review_performance', 'V') IS NOT NULL
    DROP VIEW mart.v_review_performance;
GO

/* PROJECT OVERVIEW - CURRENT MONTH ONLY */
IF OBJECT_ID('mart.v_project_overview_current', 'V') IS NOT NULL
    DROP VIEW mart.v_project_overview_current;
GO

CREATE VIEW mart.v_project_overview_current
AS
WITH latest_month AS (
    SELECT MAX(month_date_sk) AS month_date_sk
    FROM fact.project_kpi_monthly
)
SELECT
    p.project_sk,
    p.project_name,
    c.client_name,
    pt.project_type_name,
    k.month_date_sk,
    d.year_number,
    d.month_number,
    ISNULL(k.total_issues, 0) AS total_issues,
    ISNULL(k.open_issues, 0) AS open_issues,
    ISNULL(k.closed_issues, 0) AS closed_issues,
    ISNULL(k.high_priority_issues, 0) AS high_priority_issues,
    k.avg_resolution_days,
    ISNULL(k.review_count, 0) AS review_count,
    ISNULL(k.completed_reviews, 0) AS completed_reviews,
    ISNULL(k.overdue_reviews, 0) AS overdue_reviews,
    ISNULL(k.services_in_progress, 0) AS services_in_progress,
    ISNULL(k.services_completed, 0) AS services_completed,
    ISNULL(k.earned_value, 0) AS earned_value,
    ISNULL(k.claimed_to_date, 0) AS claimed_to_date,
    ISNULL(k.variance_fee, 0) AS variance_fee
FROM dim.project p
LEFT JOIN latest_month lm ON 1=1
LEFT JOIN fact.project_kpi_monthly k 
       ON k.project_sk = p.project_sk
      AND k.month_date_sk = lm.month_date_sk
LEFT JOIN dim.client c ON p.client_sk = c.client_sk
LEFT JOIN dim.project_type pt ON p.project_type_sk = pt.project_type_sk
LEFT JOIN dim.date d ON k.month_date_sk = d.date_sk
WHERE p.current_flag = 1;
GO

CREATE VIEW mart.v_review_performance
AS
SELECT
    rc.review_cycle_sk,
    s.service_name,
    p.project_name,
    c.client_name,
    pt.project_type_name,
    d_planned.[date] AS planned_date,
    d_actual.[date]  AS actual_date,
    f.status,
    f.is_completed,
    f.is_overdue,
    f.planned_vs_actual_days,
    f.issue_count_window,
    f.issue_closed_window
FROM fact.review_cycle f
JOIN dim.review_cycle rc ON f.review_cycle_sk = rc.review_cycle_sk
JOIN dim.service s ON f.service_sk = s.service_sk
JOIN dim.project p ON f.project_sk = p.project_sk
LEFT JOIN dim.client c ON f.client_sk = c.client_sk
LEFT JOIN dim.project_type pt ON f.project_type_sk = pt.project_type_sk
LEFT JOIN dim.date d_planned ON f.planned_date_sk = d_planned.date_sk
LEFT JOIN dim.date d_actual ON f.actual_date_sk = d_actual.date_sk;
GO
