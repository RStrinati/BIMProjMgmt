-- =====================================================================
-- Revit Health Project Summary
-- Aggregated health metrics per internal project
-- Author: System
-- Created: 2025-10-16
-- =====================================================================

USE RevitHealthCheckDB;
GO

-- Drop view if exists
IF OBJECT_ID('dbo.vw_RevitHealth_ProjectSummary', 'V') IS NOT NULL
    DROP VIEW dbo.vw_RevitHealth_ProjectSummary;
GO

CREATE VIEW dbo.vw_RevitHealth_ProjectSummary AS
SELECT
    pm_project_id,
    pm_project_name,
    project_status,
    project_type,
    project_sector,
    client_name,
    
    -- File Statistics
    COUNT(DISTINCT health_check_id) as total_health_checks,
    COUNT(DISTINCT revit_file_name) as unique_files,
    MAX(export_date) as latest_health_check_date,
    MIN(export_date) as earliest_health_check_date,
    
    -- Quality Aggregations
    AVG(calculated_health_score) as avg_health_score,
    MIN(calculated_health_score) as min_health_score,
    MAX(calculated_health_score) as max_health_score,
    SUM(total_warnings) as total_warnings_all_files,
    SUM(critical_warnings) as total_critical_warnings,
    
    -- File Size Aggregations
    SUM(file_size_mb) as total_model_size_mb,
    AVG(file_size_mb) as avg_file_size_mb,
    MAX(file_size_mb) as largest_file_mb,
    
    -- Element Counts
    SUM(total_elements) as total_elements_all_files,
    SUM(family_count) as total_families,
    SUM(revit_links) as total_revit_links,
    SUM(dwg_imports) as total_dwg_imports,
    
    -- Health Categories Distribution
    SUM(CASE WHEN health_category = 'Good' THEN 1 ELSE 0 END) as good_files,
    SUM(CASE WHEN health_category = 'Fair' THEN 1 ELSE 0 END) as fair_files,
    SUM(CASE WHEN health_category = 'Poor' THEN 1 ELSE 0 END) as poor_files,
    SUM(CASE WHEN health_category = 'Critical' THEN 1 ELSE 0 END) as critical_files,
    
    -- Data Freshness
    SUM(CASE WHEN data_freshness = 'Current' THEN 1 ELSE 0 END) as current_files,
    SUM(CASE WHEN data_freshness = 'Recent' THEN 1 ELSE 0 END) as recent_files,
    SUM(CASE WHEN data_freshness = 'Outdated' THEN 1 ELSE 0 END) as outdated_files,
    
    -- Risk Flags
    SUM(CASE WHEN link_health_flag != 'Clean' THEN 1 ELSE 0 END) as files_with_link_risks

FROM dbo.vw_RevitHealthWarehouse_CrossDB
WHERE mapping_status = 'Mapped'
GROUP BY 
    pm_project_id,
    pm_project_name,
    project_status,
    project_type,
    project_sector,
    client_name;

GO

PRINT 'Successfully created vw_RevitHealth_ProjectSummary';
GO
