-- Update vw_projects_full view to include new project fields
-- This script modifies the existing view to include the new columns added to the projects table

USE ProjectManagement;
GO

-- Drop and recreate the view with new columns
DROP VIEW IF EXISTS vw_projects_full;
GO

CREATE VIEW vw_projects_full AS
SELECT
    p.project_id,
    p.project_name,
    p.contract_number as project_number,
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
    pt.type_name as project_type,
    p.sector_id,
    p.method_id,
    ISNULL(ps.total_service_agreed_fee, 0) AS total_service_agreed_fee,
    ISNULL(ps.total_service_billed_amount, 0) AS total_service_billed_amount,
    CASE 
        WHEN ISNULL(ps.total_service_agreed_fee, 0) > 0 
            THEN (ISNULL(ps.total_service_billed_amount, 0) / NULLIF(ps.total_service_agreed_fee, 0)) * 100.0
        ELSE 0
    END AS service_billed_pct
FROM projects p
LEFT JOIN clients c ON p.client_id = c.client_id
LEFT JOIN project_types pt ON p.type_id = pt.type_id
LEFT JOIN (
    SELECT
        project_id,
        SUM(CAST(ISNULL(agreed_fee, 0) AS DECIMAL(18, 4))) AS total_service_agreed_fee,
        SUM(
            CAST(
                CASE 
                    WHEN ISNULL(claimed_to_date, 0) > 0 THEN ISNULL(claimed_to_date, 0)
                    WHEN ISNULL(agreed_fee, 0) > 0 THEN ISNULL(agreed_fee, 0) * (ISNULL(progress_pct, 0) / 100.0)
                    ELSE 0
                END AS DECIMAL(18, 4)
            )
        ) AS total_service_billed_amount
    FROM ProjectServices
    GROUP BY project_id
) ps ON ps.project_id = p.project_id;
GO

PRINT 'vw_projects_full view updated successfully with new project fields!';
GO
