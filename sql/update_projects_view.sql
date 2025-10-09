-- Update vw_projects_full view to include new project fields
-- This script modifies the existing view to include the new columns added to the projects table

USE ProjectManagement;
GO

-- Drop and recreate the view with new columns
IF OBJECT_ID('dbo.vw_projects_full', 'V') IS NOT NULL
    DROP VIEW dbo.vw_projects_full;
GO

CREATE VIEW dbo.vw_projects_full AS
SELECT
    p.project_id,
    p.project_name,
    c.client_name,
    c.contact_name as client_contact,
    c.contact_email,
    p.project_manager,
    p.internal_lead,
    p.contract_number,
    p.contract_value,
    p.agreed_fee,
    p.payment_terms,
    p.folder_path,
    p.ifc_folder_path,
    p.data_export_folder,
    p.start_date,
    p.end_date,
    p.status,
    p.priority,
    p.created_at,
    p.updated_at,
    -- New fields added for enhanced project creation
    p.area_hectares,
    p.mw_capacity,
    p.address,
    p.city,
    p.state,
    p.postcode,
    p.client_id,
    p.type_id,
    p.sector_id,
    p.method_id,
    -- Provide friendly names for project manager/internal lead when available
    pm.name AS project_manager_name,
    il.name AS internal_lead_name
FROM dbo.projects p
LEFT JOIN dbo.clients c ON p.client_id = c.client_id
LEFT JOIN dbo.users pm ON p.project_manager = pm.user_id
LEFT JOIN dbo.users il ON p.internal_lead = il.user_id;
GO

PRINT 'vw_projects_full view updated successfully with new project fields!';
GO