-- =====================================================================
-- Migration: Add vw_projects_summary view for Projects V2
-- =====================================================================
-- Date: 2026-01-22
-- Purpose: Provide a unified ProjectSummary record for Projects V2
-- Scope: ProjectManagement database
-- Type: Additive (non-destructive)
-- Rollback: Drop view vw_projects_summary
-- =====================================================================

USE [ProjectManagement];
GO

DROP VIEW IF EXISTS dbo.vw_projects_summary;
GO

CREATE VIEW dbo.vw_projects_summary AS
WITH service_totals AS (
    SELECT
        ps.project_id,
        COUNT(*) AS total_services,
        SUM(CASE WHEN ps.status = 'completed' THEN 1 ELSE 0 END) AS completed_services,
        SUM(CAST(ISNULL(ps.agreed_fee, 0) AS DECIMAL(18, 4))) AS total_service_agreed_fee,
        SUM(
            CAST(
                CASE
                    WHEN ISNULL(ps.claimed_to_date, 0) > 0 THEN ISNULL(ps.claimed_to_date, 0)
                    WHEN ISNULL(ps.agreed_fee, 0) > 0 THEN ISNULL(ps.agreed_fee, 0) * (ISNULL(ps.progress_pct, 0) / 100.0)
                    ELSE 0
                END AS DECIMAL(18, 4)
            )
        ) AS total_service_billed_amount
    FROM dbo.ProjectServices ps
    GROUP BY ps.project_id
),
review_totals AS (
    SELECT
        ps.project_id,
        COUNT(sr.review_id) AS total_reviews,
        SUM(CASE WHEN sr.status = 'completed' THEN 1 ELSE 0 END) AS completed_reviews
    FROM dbo.ServiceReviews sr
    INNER JOIN dbo.ProjectServices ps ON sr.service_id = ps.service_id
    GROUP BY ps.project_id
),
pipeline_totals AS (
    SELECT
        project_id,
        SUM(CASE WHEN invoice_month = FORMAT(GETDATE(), 'yyyy-MM') THEN total_amount ELSE 0 END) AS invoice_pipeline_this_month,
        SUM(CASE WHEN invoice_month = FORMAT(GETDATE(), 'yyyy-MM') THEN ready_amount ELSE 0 END) AS ready_to_invoice_this_month,
        SUM(CASE WHEN invoice_month = FORMAT(DATEADD(month, 1, GETDATE()), 'yyyy-MM') THEN total_amount ELSE 0 END) AS invoice_pipeline_next_month,
        SUM(CASE WHEN invoice_month = FORMAT(DATEADD(month, 1, GETDATE()), 'yyyy-MM') THEN ready_amount ELSE 0 END) AS ready_to_invoice_next_month
    FROM dbo.vw_invoice_pipeline_by_project_month
    GROUP BY project_id
),
finance_rollup AS (
    SELECT
        project_id,
        agreed_fee,
        billed_to_date,
        earned_value,
        earned_value_pct
    FROM dbo.vw_projects_finance_rollup
)
SELECT
    p.project_id,
    p.project_name,
    p.contract_number AS project_number,
    p.contract_number,
    p.client_id,
    c.client_name,
    p.project_manager,
    p.internal_lead,
    u.name AS internal_lead_name,
    p.status,
    p.priority,
    CASE
        WHEN ISNUMERIC(p.priority) = 1 AND CAST(p.priority AS INT) = 1 THEN 'Low'
        WHEN ISNUMERIC(p.priority) = 1 AND CAST(p.priority AS INT) = 2 THEN 'Medium'
        WHEN ISNUMERIC(p.priority) = 1 AND CAST(p.priority AS INT) = 3 THEN 'High'
        WHEN ISNUMERIC(p.priority) = 1 AND CAST(p.priority AS INT) = 4 THEN 'Critical'
        ELSE p.priority
    END AS priority_label,
    p.start_date,
    p.end_date,
    p.created_at,
    p.updated_at,
    p.type_id,
    pt.type_name AS project_type,
    COALESCE(
        CASE
            WHEN st.total_services > 0 THEN (st.completed_services * 100.0) / NULLIF(st.total_services, 0)
            WHEN rt.total_reviews > 0 THEN (rt.completed_reviews * 100.0) / NULLIF(rt.total_reviews, 0)
            ELSE NULL
        END,
        NULL
    ) AS health_pct,
    ISNULL(st.total_services, 0) AS total_services,
    ISNULL(st.completed_services, 0) AS completed_services,
    ISNULL(rt.total_reviews, 0) AS total_reviews,
    ISNULL(rt.completed_reviews, 0) AS completed_reviews,
    ISNULL(fr.agreed_fee, 0) AS agreed_fee,
    ISNULL(fr.billed_to_date, 0) AS billed_to_date,
    ISNULL(fr.earned_value, 0) AS earned_value,
    ISNULL(fr.earned_value_pct, 0) AS earned_value_pct,
    CASE
        WHEN ISNULL(fr.agreed_fee, 0) > 0
            THEN ISNULL(fr.agreed_fee, 0) - ISNULL(fr.billed_to_date, 0)
        ELSE 0
    END AS unbilled_amount,
    ISNULL(st.total_service_agreed_fee, 0) AS total_service_agreed_fee,
    ISNULL(st.total_service_billed_amount, 0) AS total_service_billed_amount,
    CASE
        WHEN ISNULL(st.total_service_agreed_fee, 0) > 0
            THEN (ISNULL(st.total_service_billed_amount, 0) / NULLIF(st.total_service_agreed_fee, 0)) * 100.0
        ELSE 0
    END AS service_billed_pct,
    ISNULL(ptot.invoice_pipeline_this_month, 0) AS invoice_pipeline_this_month,
    ISNULL(ptot.ready_to_invoice_this_month, 0) AS ready_to_invoice_this_month,
    ISNULL(ptot.invoice_pipeline_next_month, 0) AS invoice_pipeline_next_month,
    ISNULL(ptot.ready_to_invoice_next_month, 0) AS ready_to_invoice_next_month
FROM dbo.projects p
LEFT JOIN dbo.clients c ON p.client_id = c.client_id
LEFT JOIN dbo.project_types pt ON p.type_id = pt.type_id
LEFT JOIN dbo.users u ON p.internal_lead = u.user_id
LEFT JOIN service_totals st ON p.project_id = st.project_id
LEFT JOIN review_totals rt ON p.project_id = rt.project_id
LEFT JOIN finance_rollup fr ON p.project_id = fr.project_id
LEFT JOIN pipeline_totals ptot ON p.project_id = ptot.project_id;
GO

PRINT 'vw_projects_summary view created.';
GO
