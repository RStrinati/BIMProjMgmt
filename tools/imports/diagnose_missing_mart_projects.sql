-- Diagnose why only 2 projects appear in mart views when dim.project has all projects
USE ProjectManagement;
GO

PRINT '=== 1. Count projects in dimension vs marts ===';
SELECT 'dim.project (current)' AS source, COUNT(DISTINCT project_sk) AS project_count
FROM dim.project
WHERE current_flag = 1
UNION ALL
SELECT 'mart.v_project_overview', COUNT(DISTINCT project_sk)
FROM mart.v_project_overview
UNION ALL
SELECT 'mart.v_issue_trends', COUNT(DISTINCT p.project_sk)
FROM mart.v_issue_trends v
LEFT JOIN dim.project p ON p.project_name = v.project_name AND p.current_flag = 1
UNION ALL
SELECT 'mart.v_review_performance', COUNT(DISTINCT project_sk)
FROM mart.v_review_performance;
GO

PRINT '=== 2. Which projects are in dim.project but NOT in marts? ===';
SELECT 
    p.project_sk,
    p.project_bk,
    p.project_name,
    p.status,
    p.created_at
FROM dim.project p
WHERE p.current_flag = 1
  AND NOT EXISTS (
      SELECT 1 FROM mart.v_project_overview m WHERE m.project_sk = p.project_sk
  )
ORDER BY p.project_name;
GO

PRINT '=== 3. Check fact table coverage ===';
SELECT 'fact.project_kpi_monthly' AS fact_table, COUNT(DISTINCT project_sk) AS project_count
FROM fact.project_kpi_monthly
UNION ALL
SELECT 'fact.issue_snapshot', COUNT(DISTINCT project_sk)
FROM fact.issue_snapshot
UNION ALL
SELECT 'fact.review_cycle', COUNT(DISTINCT project_sk)
FROM fact.review_cycle
UNION ALL
SELECT 'fact.service_monthly', COUNT(DISTINCT project_sk)
FROM fact.service_monthly;
GO

PRINT '=== 4. Projects in dim.project but missing from fact.project_kpi_monthly ===';
SELECT 
    p.project_sk,
    p.project_bk,
    p.project_name,
    p.status,
    'Missing from fact.project_kpi_monthly' AS reason
FROM dim.project p
WHERE p.current_flag = 1
  AND NOT EXISTS (
      SELECT 1 FROM fact.project_kpi_monthly f WHERE f.project_sk = p.project_sk
  )
ORDER BY p.project_name;
GO

PRINT '=== 5. Check staging tables for project presence ===';
SELECT 'stg.projects' AS source, COUNT(DISTINCT project_id) AS project_count
FROM stg.projects
UNION ALL
SELECT 'stg.project_services', COUNT(DISTINCT project_id)
FROM stg.project_services
UNION ALL
SELECT 'stg.service_reviews', COUNT(DISTINCT s.project_id)
FROM stg.service_reviews sr
JOIN stg.project_services s ON sr.service_id = s.service_id
UNION ALL
SELECT 'stg.issues (distinct project_id_raw)', COUNT(DISTINCT TRY_CONVERT(INT, project_id_raw))
FROM stg.issues
WHERE TRY_CONVERT(INT, project_id_raw) IS NOT NULL;
GO

PRINT '=== 6. Projects with no issues ===';
SELECT 
    p.project_sk,
    p.project_bk,
    p.project_name,
    (SELECT COUNT(*) FROM dim.issue i WHERE i.project_sk = p.project_sk) AS issue_count
FROM dim.project p
WHERE p.current_flag = 1
  AND NOT EXISTS (
      SELECT 1 FROM dim.issue i WHERE i.project_sk = p.project_sk
  )
ORDER BY p.project_name;
GO

PRINT '=== 7. Projects with no services ===';
SELECT 
    p.project_sk,
    p.project_bk,
    p.project_name,
    (SELECT COUNT(*) FROM dim.service s WHERE s.project_sk = p.project_sk) AS service_count
FROM dim.project p
WHERE p.current_flag = 1
  AND NOT EXISTS (
      SELECT 1 FROM dim.service s WHERE s.project_sk = p.project_sk
  )
ORDER BY p.project_name;
GO

PRINT '=== 8. Root cause summary ===';
SELECT 
    p.project_sk,
    p.project_bk,
    p.project_name,
    (SELECT COUNT(*) FROM dim.issue i WHERE i.project_sk = p.project_sk) AS issue_count,
    (SELECT COUNT(*) FROM dim.service s WHERE s.project_sk = p.project_sk) AS service_count,
    (SELECT COUNT(*) FROM dim.review_cycle rc 
     JOIN dim.service s ON rc.service_sk = s.service_sk 
     WHERE s.project_sk = p.project_sk) AS review_count,
    CASE 
        WHEN NOT EXISTS (SELECT 1 FROM fact.project_kpi_monthly f WHERE f.project_sk = p.project_sk)
        THEN 'Missing from fact.project_kpi_monthly (drives mart.v_project_overview)'
        ELSE 'Has fact row'
    END AS status
FROM dim.project p
WHERE p.current_flag = 1
ORDER BY p.project_name;
GO
