/*
    Seed staging from ProjectManagement OLTP tables
    - Projects, Services, Service Reviews
*/

USE ProjectManagement;
GO

-- Projects (minimal fields available in dbo.Projects)
INSERT INTO stg.projects (
    project_id,
    project_name,
    client_id,
    project_type_id,
    status,
    priority,
    start_date,
    end_date,
    created_at,
    updated_at,
    record_source
)
SELECT
    p.project_id,
    p.project_name,
    NULL AS client_id,
    NULL AS project_type_id,
    p.status,
    p.priority,
    p.start_date,
    p.end_date,
    p.created_at,
    p.updated_at,
    'seed_from_pm.sql'
FROM dbo.Projects p;

PRINT 'Seeded stg.projects from dbo.Projects';
GO

-- Project Services
INSERT INTO stg.project_services (
    service_id,
    project_id,
    service_code,
    service_name,
    phase,
    unit_type,
    unit_qty,
    unit_rate,
    lump_sum_fee,
    agreed_fee,
    progress_pct,
    claimed_to_date,
    status,
    created_at,
    updated_at,
    record_source
)
SELECT
    ps.service_id,
    ps.project_id,
    ps.service_code,
    ps.service_name,
    ps.phase,
    ps.unit_type,
    ps.unit_qty,
    ps.unit_rate,
    ps.lump_sum_fee,
    ps.agreed_fee,
    ps.progress_pct,
    ps.claimed_to_date,
    ps.status,
    ps.created_at,
    ps.updated_at,
    'seed_from_pm.sql'
FROM dbo.ProjectServices ps;

PRINT 'Seeded stg.project_services from dbo.ProjectServices';
GO

-- Service Reviews
INSERT INTO stg.service_reviews (
    review_id,
    service_id,
    cycle_no,
    planned_date,
    due_date,
    actual_date,
    status,
    disciplines,
    deliverables,
    weight_factor,
    evidence_links,
    record_source
)
SELECT
    sr.review_id,
    sr.service_id,
    sr.cycle_no,
    sr.planned_date,
    sr.due_date,
    sr.actual_issued_at AS actual_date,
    sr.status,
    sr.disciplines,
    sr.deliverables,
    sr.weight_factor,
    sr.evidence_links,
    'seed_from_pm.sql'
FROM dbo.ServiceReviews sr;

PRINT 'Seeded stg.service_reviews from dbo.ServiceReviews';
GO
