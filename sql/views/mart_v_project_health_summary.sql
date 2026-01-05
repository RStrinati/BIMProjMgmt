-- =============================================
-- Analytical Mart: mart.v_project_health_summary
-- Description: Project-level health summary with aggregated metrics and compliance tracking
-- Dependencies: fact.revit_health_daily, dim.revit_file, dbo.projects, dbo.clients
-- Author: Data Warehouse Team
-- Date: 2025-12-04
-- =============================================

USE ProjectManagement;
GO

-- Create schema if not exists
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'mart')
BEGIN
    EXEC('CREATE SCHEMA mart');
    PRINT 'Created schema: mart';
END
GO

-- Drop existing view
IF OBJECT_ID('mart.v_project_health_summary', 'V') IS NOT NULL
BEGIN
    DROP VIEW mart.v_project_health_summary;
    PRINT 'Dropped existing view: mart.v_project_health_summary';
END
GO

CREATE VIEW mart.v_project_health_summary AS
WITH LatestHealthPerFile AS (
    -- Get the most recent health check for each file
    SELECT 
        project_key,
        file_name_key,
        health_fact_id,
        ROW_NUMBER() OVER (
            PARTITION BY project_key, file_name_key 
            ORDER BY date_key DESC, health_fact_id DESC
        ) as rn
    FROM fact.revit_health_daily
),
LatestFacts AS (
    SELECT f.*
    FROM fact.revit_health_daily f
    INNER JOIN LatestHealthPerFile latest 
        ON f.health_fact_id = latest.health_fact_id
    WHERE latest.rn = 1
)
SELECT 
    -- === PROJECT IDENTIFICATION ===
    p.project_id,
    p.project_name,
    c.client_name,
    p.status as project_status,
    p.priority as project_priority,
    
    -- === FILE COUNTS ===
    COUNT(DISTINCT f.file_name_key) as total_files,
    COUNT(DISTINCT CASE WHEN f.is_control_model = 1 THEN f.file_name_key END) as control_model_files,
    COUNT(DISTINCT CASE WHEN df.discipline_code = 'A' THEN f.file_name_key END) as architecture_files,
    COUNT(DISTINCT CASE WHEN df.discipline_code = 'S' THEN f.file_name_key END) as structural_files,
    COUNT(DISTINCT CASE WHEN df.discipline_code = 'M' THEN f.file_name_key END) as mechanical_files,
    COUNT(DISTINCT CASE WHEN df.discipline_code = 'E' THEN f.file_name_key END) as electrical_files,
    COUNT(DISTINCT CASE WHEN df.discipline_code = 'P' THEN f.file_name_key END) as plumbing_files,
    
    -- === HEALTH SCORE AGGREGATIONS ===
    CAST(AVG(CAST(f.health_score AS FLOAT)) AS DECIMAL(5,2)) as avg_health_score,
    MIN(f.health_score) as min_health_score,
    MAX(f.health_score) as max_health_score,
    
    -- === HEALTH CATEGORY DISTRIBUTION ===
    SUM(CASE WHEN f.health_category = 'Good' THEN 1 ELSE 0 END) as good_files,
    SUM(CASE WHEN f.health_category = 'Fair' THEN 1 ELSE 0 END) as fair_files,
    SUM(CASE WHEN f.health_category = 'Poor' THEN 1 ELSE 0 END) as poor_files,
    SUM(CASE WHEN f.health_category = 'Critical' THEN 1 ELSE 0 END) as critical_files,
    
    -- === WARNING AGGREGATIONS ===
    SUM(f.total_warnings) as total_warnings,
    SUM(f.critical_warnings) as total_critical_warnings,
    CAST(AVG(CAST(f.total_warnings AS FLOAT)) AS DECIMAL(10,2)) as avg_warnings_per_file,
    CAST(AVG(CAST(f.critical_warnings AS FLOAT)) AS DECIMAL(10,2)) as avg_critical_per_file,
    
    -- === FILE SIZE METRICS ===
    SUM(f.file_size_mb) as total_file_size_mb,
    CAST(AVG(f.file_size_mb) AS DECIMAL(10,2)) as avg_file_size_mb,
    MAX(f.file_size_mb) as max_file_size_mb,
    SUM(CASE WHEN f.file_size_category = 'Very Large' THEN 1 ELSE 0 END) as very_large_files,
    
    -- === ELEMENT METRICS ===
    SUM(f.total_elements) as total_elements,
    SUM(f.family_count) as total_families,
    CAST(AVG(f.warnings_per_1000_elements) AS DECIMAL(10,2)) as avg_warnings_per_1k_elements,
    
    -- === VIEW EFFICIENCY ===
    CAST(AVG(f.view_efficiency_pct) AS DECIMAL(5,2)) as avg_view_efficiency_pct,
    SUM(f.total_views) as total_views,
    SUM(f.views_not_on_sheets) as total_views_not_on_sheets,
    
    -- === LINK HEALTH ===
    SUM(f.revit_links) as total_revit_links,
    SUM(f.dwg_imports) as total_dwg_imports,
    SUM(f.dwg_links) as total_dwg_links,
    SUM(CASE WHEN f.link_health_flag LIKE '%Issue%' THEN 1 ELSE 0 END) as files_with_link_issues,
    
    -- === NAMING COMPLIANCE ===
    CAST(SUM(CASE WHEN f.naming_valid = 1 THEN 1 ELSE 0 END) * 100.0 / 
         NULLIF(COUNT(*), 0) AS DECIMAL(5,2)) as naming_compliance_pct,
    SUM(CASE WHEN f.naming_valid = 0 THEN 1 ELSE 0 END) as files_with_naming_issues,
    
    -- === COORDINATE ALIGNMENT COMPLIANCE ===
    CAST(SUM(CASE WHEN f.coordinates_aligned = 1 THEN 1 ELSE 0 END) * 100.0 / 
         NULLIF(COUNT(*), 0) AS DECIMAL(5,2)) as coordinates_compliance_pct,
    SUM(CASE WHEN f.coordinates_aligned = 0 THEN 1 ELSE 0 END) as files_with_coordinate_issues,
    
    -- === GRID ALIGNMENT COMPLIANCE ===
    CAST(SUM(CASE WHEN f.grids_aligned = 1 THEN 1 ELSE 0 END) * 100.0 / 
         NULLIF(COUNT(*), 0) AS DECIMAL(5,2)) as grids_compliance_pct,
    SUM(CASE WHEN f.grids_aligned = 0 THEN 1 ELSE 0 END) as files_with_grid_issues,
    
    -- === LEVEL ALIGNMENT COMPLIANCE ===
    CAST(SUM(CASE WHEN f.levels_aligned = 1 THEN 1 ELSE 0 END) * 100.0 / 
         NULLIF(COUNT(*), 0) AS DECIMAL(5,2)) as levels_compliance_pct,
    SUM(CASE WHEN f.levels_aligned = 0 THEN 1 ELSE 0 END) as files_with_level_issues,
    
    -- === OVERALL COMPLIANCE ===
    CAST(SUM(CASE WHEN f.naming_valid = 1 
                   AND f.coordinates_aligned = 1 
                   AND f.grids_aligned = 1 
                   AND f.levels_aligned = 1 
              THEN 1 ELSE 0 END) * 100.0 / 
         NULLIF(COUNT(*), 0) AS DECIMAL(5,2)) as overall_compliance_pct,
    
    -- === DATA FRESHNESS ===
    MAX(f.export_datetime) as last_health_check_date,
    CAST(AVG(CAST(f.days_since_export AS FLOAT)) AS DECIMAL(5,1)) as avg_days_since_export,
    SUM(CASE WHEN f.data_freshness IN ('Stale', 'Very Stale') THEN 1 ELSE 0 END) as files_with_stale_data,
    
    -- === METADATA ===
    MAX(f.loaded_at) as last_warehouse_update
    
FROM LatestFacts f
LEFT JOIN dbo.projects p 
    ON f.project_key = p.project_id
LEFT JOIN dbo.clients c 
    ON p.client_id = c.client_id
INNER JOIN dim.revit_file df 
    ON f.file_name_key = df.revit_file_key 
    AND df.current_flag = 1

GROUP BY 
    p.project_id,
    p.project_name,
    c.client_name,
    p.status,
    p.priority;
GO

-- Add view description
EXEC sys.sp_addextendedproperty 
    @name=N'MS_Description', 
    @value=N'Project-level health summary with aggregated metrics for file counts, health scores, warnings, compliance tracking, and data freshness. Uses latest health check per file.', 
    @level0type=N'SCHEMA', @level0name=N'mart', 
    @level1type=N'VIEW', @level1name=N'v_project_health_summary';
GO

PRINT 'Successfully created view: mart.v_project_health_summary';
GO

-- Test query (optional)
-- SELECT TOP 5 * FROM mart.v_project_health_summary ORDER BY avg_health_score ASC;
