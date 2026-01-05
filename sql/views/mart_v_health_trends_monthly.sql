-- =============================================
-- Analytical Mart: mart.v_health_trends_monthly
-- Description: Monthly health trend analysis by project and discipline
-- Dependencies: fact.revit_health_daily, dim.revit_file, dbo.projects
-- Author: Data Warehouse Team
-- Date: 2025-12-04
-- =============================================

USE ProjectManagement;
GO

-- Drop existing view
IF OBJECT_ID('mart.v_health_trends_monthly', 'V') IS NOT NULL
BEGIN
    DROP VIEW mart.v_health_trends_monthly;
    PRINT 'Dropped existing view: mart.v_health_trends_monthly';
END
GO

CREATE VIEW mart.v_health_trends_monthly AS
WITH DateDimension AS (
    -- Create date dimension attributes from export_datetime
    SELECT DISTINCT
        f.date_key,
        f.export_datetime,
        YEAR(f.export_datetime) as year_number,
        MONTH(f.export_datetime) as month_number,
        DATENAME(MONTH, f.export_datetime) as month_name,
        FORMAT(f.export_datetime, 'yyyy-MM') as year_month,
        FORMAT(f.export_datetime, 'MMM yyyy') as year_month_name,
        DATEPART(QUARTER, f.export_datetime) as quarter_number,
        CONCAT('Q', DATEPART(QUARTER, f.export_datetime), ' ', YEAR(f.export_datetime)) as quarter_name
    FROM fact.revit_health_daily f
)
SELECT 
    -- === TIME DIMENSIONS ===
    d.year_number,
    d.month_number,
    d.month_name,
    d.year_month,
    d.year_month_name,
    d.quarter_number,
    d.quarter_name,
    
    -- === PROJECT ATTRIBUTES ===
    p.project_id,
    p.project_name,
    p.status as project_status,
    
    -- === DISCIPLINE BREAKDOWN ===
    df.discipline_code,
    df.discipline_full_name,
    
    -- === FILE COUNTS ===
    COUNT(DISTINCT f.file_name_key) as files_checked,
    COUNT(DISTINCT CASE WHEN f.is_control_model = 1 THEN f.file_name_key END) as control_model_files,
    
    -- === HEALTH SCORE TRENDS ===
    CAST(AVG(CAST(f.health_score AS FLOAT)) AS DECIMAL(5,2)) as avg_health_score,
    MIN(f.health_score) as min_health_score,
    MAX(f.health_score) as max_health_score,
    STDEV(f.health_score) as health_score_stddev,
    
    -- === HEALTH CATEGORY DISTRIBUTION ===
    SUM(CASE WHEN f.health_category = 'Good' THEN 1 ELSE 0 END) as good_count,
    SUM(CASE WHEN f.health_category = 'Fair' THEN 1 ELSE 0 END) as fair_count,
    SUM(CASE WHEN f.health_category = 'Poor' THEN 1 ELSE 0 END) as poor_count,
    SUM(CASE WHEN f.health_category = 'Critical' THEN 1 ELSE 0 END) as critical_count,
    
    -- === WARNING TRENDS ===
    SUM(f.total_warnings) as total_warnings,
    SUM(f.critical_warnings) as total_critical_warnings,
    CAST(AVG(CAST(f.total_warnings AS FLOAT)) AS DECIMAL(10,2)) as avg_warnings_per_file,
    CAST(AVG(f.warnings_per_1000_elements) AS DECIMAL(10,2)) as avg_warnings_per_1k_elements,
    
    -- === FILE SIZE TRENDS ===
    CAST(AVG(f.file_size_mb) AS DECIMAL(10,2)) as avg_file_size_mb,
    MAX(f.file_size_mb) as max_file_size_mb,
    SUM(CASE WHEN f.file_size_category = 'Very Large' THEN 1 ELSE 0 END) as very_large_files,
    
    -- === ELEMENT TRENDS ===
    CAST(AVG(CAST(f.total_elements AS FLOAT)) AS DECIMAL(10,0)) as avg_total_elements,
    CAST(AVG(CAST(f.family_count AS FLOAT)) AS DECIMAL(10,0)) as avg_family_count,
    
    -- === VIEW EFFICIENCY TRENDS ===
    CAST(AVG(f.view_efficiency_pct) AS DECIMAL(5,2)) as avg_view_efficiency_pct,
    CAST(AVG(CAST(f.total_views AS FLOAT)) AS DECIMAL(10,1)) as avg_total_views,
    
    -- === COMPLIANCE TRENDS ===
    CAST(AVG(CAST(f.naming_valid AS FLOAT)) * 100 AS DECIMAL(5,2)) as naming_compliance_pct,
    CAST(AVG(CAST(f.coordinates_aligned AS FLOAT)) * 100 AS DECIMAL(5,2)) as coordinates_compliance_pct,
    CAST(AVG(CAST(f.grids_aligned AS FLOAT)) * 100 AS DECIMAL(5,2)) as grids_compliance_pct,
    CAST(AVG(CAST(f.levels_aligned AS FLOAT)) * 100 AS DECIMAL(5,2)) as levels_compliance_pct,
    
    -- === OVERALL COMPLIANCE ===
    CAST(SUM(CASE WHEN f.naming_valid = 1 
                   AND f.coordinates_aligned = 1 
                   AND f.grids_aligned = 1 
                   AND f.levels_aligned = 1 
              THEN 1 ELSE 0 END) * 100.0 / 
         NULLIF(COUNT(*), 0) AS DECIMAL(5,2)) as overall_compliance_pct,
    
    -- === LINK HEALTH TRENDS ===
    CAST(AVG(CAST(f.revit_links AS FLOAT)) AS DECIMAL(5,2)) as avg_revit_links,
    CAST(AVG(CAST(f.dwg_imports AS FLOAT)) AS DECIMAL(5,2)) as avg_dwg_imports,
    SUM(CASE WHEN f.link_health_flag LIKE '%Issue%' THEN 1 ELSE 0 END) as files_with_link_issues,
    
    -- === DATA FRESHNESS ===
    CAST(AVG(CAST(f.days_since_export AS FLOAT)) AS DECIMAL(5,1)) as avg_days_since_export,
    
    -- === MONTH-OVER-MONTH COMPARISON ===
    -- These would require LAG/LEAD but simplified for now
    COUNT(*) as total_health_checks
    
FROM fact.revit_health_daily f
INNER JOIN DateDimension d 
    ON f.date_key = d.date_key
LEFT JOIN dbo.projects p 
    ON f.project_key = p.project_id
INNER JOIN dim.revit_file df 
    ON f.file_name_key = df.revit_file_key 
    AND df.current_flag = 1

GROUP BY 
    d.year_number,
    d.month_number,
    d.month_name,
    d.year_month,
    d.year_month_name,
    d.quarter_number,
    d.quarter_name,
    p.project_id,
    p.project_name,
    p.status,
    df.discipline_code,
    df.discipline_full_name;
GO

-- Add view description
EXEC sys.sp_addextendedproperty 
    @name=N'MS_Description', 
    @value=N'Monthly health trend analysis by project and discipline. Provides time-series metrics for health scores, warnings, compliance, file sizes, and view efficiency. Supports trend analysis and MoM comparisons.', 
    @level0type=N'SCHEMA', @level0name=N'mart', 
    @level1type=N'VIEW', @level1name=N'v_health_trends_monthly';
GO

PRINT 'Successfully created view: mart.v_health_trends_monthly';
GO

-- Test query (optional)
-- SELECT TOP 10 * FROM mart.v_health_trends_monthly 
-- ORDER BY year_number DESC, month_number DESC, avg_health_score ASC;
