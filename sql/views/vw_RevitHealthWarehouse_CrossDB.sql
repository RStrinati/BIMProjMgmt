-- =====================================================================
-- Revit Health Warehouse - Cross-Database Integration
-- Links RevitHealthCheckDB data with ProjectManagement projects via aliases
-- Author: System
-- Created: 2025-10-16
-- =====================================================================

USE RevitHealthCheckDB;
GO

-- Drop view if exists
IF OBJECT_ID('dbo.vw_RevitHealthWarehouse_CrossDB', 'V') IS NOT NULL
    DROP VIEW dbo.vw_RevitHealthWarehouse_CrossDB;
GO

CREATE VIEW dbo.vw_RevitHealthWarehouse_CrossDB AS
WITH LatestFiles AS (
    -- Use existing vw_LatestRvtFiles which already has latest file selection logic
    SELECT 
        lf.nId,
        lf.strRvtFileName,
        lf.pm_project_id,
        lf.project_name as pm_project_name,
        lf.model_functional_code,
        lf.NormalizedFileName,
        p.status as project_status,
        p.priority as project_priority,
        p.project_manager,
        p.client_id,
        c.client_name,
        pt.type_name as project_type,
        s.sector_name as project_sector
    FROM dbo.vw_LatestRvtFiles lf
    LEFT JOIN ProjectManagement.dbo.projects p ON lf.pm_project_id = p.project_id
    LEFT JOIN ProjectManagement.dbo.clients c ON p.client_id = c.client_id
    LEFT JOIN ProjectManagement.dbo.project_types pt ON p.type_id = pt.type_id
    LEFT JOIN ProjectManagement.dbo.sectors s ON p.sector_id = s.sector_id
)
SELECT 
    -- === IDENTITY & REFERENCE ===
    h.nId as health_check_id,
    h.strRvtFileName as revit_file_name,
    lf.NormalizedFileName as normalized_file_name,
    h.strProjectName as revit_project_name,
    h.strProjectNumber as revit_project_number,
    lf.model_functional_code,
    
    -- === PROJECT MANAGEMENT LINKAGE ===
    lf.pm_project_id,
    lf.pm_project_name,
    lf.project_status,
    lf.project_priority,
    lf.project_manager,
    lf.client_id,
    lf.client_name,
    lf.project_type,
    lf.project_sector,
    
    -- === MAPPING STATUS ===
    CASE 
        WHEN lf.pm_project_id IS NOT NULL THEN 'Mapped'
        ELSE 'Unmapped'
    END as mapping_status,
    
    -- === REVIT METADATA ===
    h.strClientName as revit_client_name,
    u.rvtUserName as revit_user,
    s.sysUserName as system_user_name,
    h.strRvtVersion as revit_version,
    h.strRvtBuildVersion as build_version,
    
    -- === TEMPORAL DIMENSIONS ===
    h.ConvertedExportedDate as export_date,
    CAST(h.ConvertedExportedDate AS DATE) as export_date_key,
    DATEPART(YEAR, h.ConvertedExportedDate) as export_year,
    DATEPART(QUARTER, h.ConvertedExportedDate) as export_quarter,
    DATEPART(MONTH, h.ConvertedExportedDate) as export_month,
    DATENAME(MONTH, h.ConvertedExportedDate) as export_month_name,
    DATEDIFF(DAY, h.ConvertedExportedDate, GETDATE()) as days_since_export,
    
    -- === FILE SIZE METRICS ===
    h.nModelFileSizeMB as file_size_mb,
    CASE 
        WHEN h.nModelFileSizeMB < 100 THEN 'Small (<100MB)'
        WHEN h.nModelFileSizeMB < 300 THEN 'Medium (100-300MB)'
        WHEN h.nModelFileSizeMB < 500 THEN 'Large (300-500MB)'
        ELSE 'Very Large (>500MB)'
    END as file_size_category,
    
    -- === QUALITY METRICS ===
    h.nWarningsCount as total_warnings,
    h.nCriticalWarningsCount as critical_warnings,
    
    -- Health Score Calculation
    CASE 
        WHEN h.nWarningsCount = 0 THEN 100
        WHEN h.nCriticalWarningsCount > 50 THEN 0
        ELSE CAST(100 - (
            (CAST(h.nWarningsCount AS FLOAT) * 0.5) + 
            (CAST(h.nCriticalWarningsCount AS FLOAT) * 2.0)
        ) / 10 AS INT)
    END as calculated_health_score,
    
    CASE 
        WHEN h.nCriticalWarningsCount > 50 THEN 'Critical'
        WHEN h.nWarningsCount > 100 THEN 'Poor'
        WHEN h.nWarningsCount > 50 THEN 'Fair'
        ELSE 'Good'
    END as health_category,
    
    -- === VIEW METRICS ===
    h.nTotalViewCount as total_views,
    h.nCopiedViewCount as copied_views,
    h.nDependentViewCount as dependent_views,
    h.nViewsNotOnSheetsCount as views_not_on_sheets,
    h.nViewTemplateCount as view_templates,
    
    -- View Efficiency Score
    CASE 
        WHEN h.nTotalViewCount > 0 
        THEN CAST((h.nTotalViewCount - ISNULL(h.nViewsNotOnSheetsCount, 0)) * 100.0 / h.nTotalViewCount AS DECIMAL(5,2))
        ELSE 0 
    END as view_efficiency_pct,
    
    -- === ELEMENT & LINK METRICS ===
    h.nTotalElementsCount as total_elements,
    h.nFamilyCount as family_count,
    h.nGroupCount as group_count,
    h.nInPlaceFamiliesCount as inplace_families,
    h.nSketchupImportsCount as sketchup_imports,
    h.nRvtLinkCount as revit_links,
    h.nDwgLinkCount as dwg_links,
    h.nDwgImportCount as dwg_imports,
    h.nSheetsCount as sheet_count,
    h.nDesignOptionSetCount as design_option_sets,
    h.nDesignOptionCount as design_options,
    
    -- === VALIDATION & FLAGS ===
    h.validation_status,
    h.validation_reason,
    h.discipline_code,
    h.discipline_full_name,
    
    CASE 
        WHEN h.nDwgImportCount > 10 THEN 'High CAD Import Risk'
        WHEN h.nSketchupImportsCount > 0 THEN 'SketchUp Imports Present'
        ELSE 'Clean'
    END as link_health_flag,
    
    CASE 
        WHEN DATEDIFF(DAY, h.ConvertedExportedDate, GETDATE()) <= 7 THEN 'Current'
        WHEN DATEDIFF(DAY, h.ConvertedExportedDate, GETDATE()) <= 30 THEN 'Recent'
        ELSE 'Outdated'
    END as data_freshness,
    
    -- === JSON PAYLOADS (for drill-down) ===
    h.jsonWarnings as warnings_json,
    h.jsonViews as views_json,
    h.jsonFamilies as families_json,
    h.jsonFamily_sizes as family_sizes_json,
    h.jsonLevels as levels_json,
    h.jsonPhases as phases_json,
    h.jsonSchedules as schedules_json,
    h.jsonWorksets as worksets_json

FROM dbo.tblRvtProjHealth h
INNER JOIN LatestFiles lf ON h.nId = lf.nId
LEFT JOIN dbo.tblRvtUser u ON h.nRvtUserId = u.nId
LEFT JOIN dbo.tblSysName s ON h.nSysNameId = s.nId
WHERE h.nDeletedOn IS NULL;

GO

-- Performance Indexes (with correct SET options)
SET QUOTED_IDENTIFIER ON;
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_tblRvtProjHealth_FileName' AND object_id = OBJECT_ID('dbo.tblRvtProjHealth'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_tblRvtProjHealth_FileName
        ON dbo.tblRvtProjHealth(strRvtFileName)
        INCLUDE (nWarningsCount, nCriticalWarningsCount, nModelFileSizeMB)
        WHERE nDeletedOn IS NULL;
    PRINT 'Created index IX_tblRvtProjHealth_FileName';
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_tblRvtProjHealth_ProjectMapping' AND object_id = OBJECT_ID('dbo.tblRvtProjHealth'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_tblRvtProjHealth_ProjectMapping
        ON dbo.tblRvtProjHealth(strRvtFileName, strProjectName, strProjectNumber)
        WHERE nDeletedOn IS NULL;
    PRINT 'Created index IX_tblRvtProjHealth_ProjectMapping';
END
GO

PRINT 'Successfully created vw_RevitHealthWarehouse_CrossDB and indexes';
GO
