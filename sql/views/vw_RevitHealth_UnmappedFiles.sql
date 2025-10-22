-- =====================================================================
-- Unmapped Revit Files - Discovery & Alias Suggestions
-- Identifies Revit files without project mappings
-- Author: System
-- Created: 2025-10-16
-- =====================================================================

USE RevitHealthCheckDB;
GO

-- Drop view if exists
IF OBJECT_ID('dbo.vw_RevitHealth_UnmappedFiles', 'V') IS NOT NULL
    DROP VIEW dbo.vw_RevitHealth_UnmappedFiles;
GO

CREATE VIEW dbo.vw_RevitHealth_UnmappedFiles AS
SELECT
    w.health_check_id,
    w.revit_file_name,
    w.revit_project_name,
    w.revit_project_number,
    w.revit_client_name,
    w.export_date,
    w.total_warnings,
    w.critical_warnings,
    w.file_size_mb,
    w.calculated_health_score,
    w.health_category,
    
    -- Suggested Mapping (fuzzy match logic)
    (
        SELECT TOP 1 p.project_id
        FROM ProjectManagement.dbo.projects p
        WHERE 
            SOUNDEX(p.project_name) = SOUNDEX(w.revit_project_name) OR
            p.project_name LIKE '%' + w.revit_project_number + '%' OR
            p.contract_number = w.revit_project_number OR
            p.project_name LIKE '%' + w.revit_project_name + '%'
        ORDER BY 
            CASE 
                WHEN p.project_name = w.revit_project_name THEN 1
                WHEN p.contract_number = w.revit_project_number THEN 2
                WHEN p.project_name LIKE '%' + w.revit_project_number + '%' THEN 3
                ELSE 4 
            END,
            p.created_at DESC
    ) as suggested_project_id,
    
    (
        SELECT TOP 1 p.project_name
        FROM ProjectManagement.dbo.projects p
        WHERE 
            SOUNDEX(p.project_name) = SOUNDEX(w.revit_project_name) OR
            p.project_name LIKE '%' + w.revit_project_number + '%' OR
            p.contract_number = w.revit_project_number OR
            p.project_name LIKE '%' + w.revit_project_name + '%'
        ORDER BY 
            CASE 
                WHEN p.project_name = w.revit_project_name THEN 1
                WHEN p.contract_number = w.revit_project_number THEN 2
                WHEN p.project_name LIKE '%' + w.revit_project_number + '%' THEN 3
                ELSE 4 
            END,
            p.created_at DESC
    ) as suggested_project_name,
    
    -- Confidence Score
    (
        SELECT TOP 1 
            CASE 
                WHEN p.project_name = w.revit_project_name THEN 95
                WHEN p.contract_number = w.revit_project_number THEN 90
                WHEN p.project_name LIKE '%' + w.revit_project_number + '%' THEN 75
                WHEN SOUNDEX(p.project_name) = SOUNDEX(w.revit_project_name) THEN 60
                ELSE 40 
            END
        FROM ProjectManagement.dbo.projects p
        WHERE 
            SOUNDEX(p.project_name) = SOUNDEX(w.revit_project_name) OR
            p.project_name LIKE '%' + w.revit_project_number + '%' OR
            p.contract_number = w.revit_project_number OR
            p.project_name LIKE '%' + w.revit_project_name + '%'
        ORDER BY 
            CASE 
                WHEN p.project_name = w.revit_project_name THEN 1
                WHEN p.contract_number = w.revit_project_number THEN 2
                WHEN p.project_name LIKE '%' + w.revit_project_number + '%' THEN 3
                ELSE 4 
            END,
            p.created_at DESC
    ) as match_confidence

FROM dbo.vw_RevitHealthWarehouse_CrossDB w
WHERE mapping_status = 'Unmapped'
  AND data_freshness IN ('Current', 'Recent');

GO

PRINT 'Successfully created vw_RevitHealth_UnmappedFiles';
GO
