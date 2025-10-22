-- Add naming_convention column to projects table
-- This allows projects to override the client's default naming convention

USE ProjectManagement;


-- Check if column exists before adding
IF NOT EXISTS (
    SELECT 1 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'projects' 
    AND COLUMN_NAME = 'naming_convention'
)
BEGIN
    PRINT 'Adding naming_convention column to projects table...';
    
    ALTER TABLE projects
    ADD naming_convention NVARCHAR(50) NULL;
    
    -- Add check constraint to ensure valid convention codes
    ALTER TABLE projects
    ADD CONSTRAINT CK_projects_naming_convention 
    CHECK (naming_convention IS NULL OR naming_convention IN ('AWS', 'SINSW'));
    
    PRINT '✅ naming_convention column added to projects table';
END
ELSE
BEGIN
    PRINT 'ℹ️ naming_convention column already exists in projects table';
END


-- Update the view to include naming_convention
PRINT 'Updating vw_projects_full view...';


DROP VIEW IF EXISTS vw_projects_full;


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
    -- Enhanced project fields
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
    -- Naming convention (project override or client default)
    COALESCE(p.naming_convention, c.naming_convention) as naming_convention
FROM projects p
LEFT JOIN clients c ON p.client_id = c.client_id
LEFT JOIN project_types pt ON p.type_id = pt.type_id;


PRINT '✅ vw_projects_full view updated with naming_convention';


PRINT '';
PRINT '========================================';
PRINT 'Migration Complete!';
PRINT '========================================';
PRINT '';
PRINT 'Changes made:';
PRINT '  1. Added naming_convention column to projects table';
PRINT '  2. Added check constraint for valid convention codes';
PRINT '  3. Updated vw_projects_full view to include naming_convention';
PRINT '';
PRINT 'The view uses COALESCE to:';
PRINT '  - Return project.naming_convention if set (override)';
PRINT '  - Fall back to client.naming_convention if project value is NULL';
PRINT '';
