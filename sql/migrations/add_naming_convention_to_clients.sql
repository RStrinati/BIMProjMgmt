-- Add naming_convention column to clients table
-- This allows storing the client-specific naming convention (e.g., 'AWS', 'SINSW')

USE ProjectManagement;
GO

-- Check if column exists, add if not
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'clients' 
    AND COLUMN_NAME = 'naming_convention'
)
BEGIN
    ALTER TABLE dbo.clients 
    ADD naming_convention NVARCHAR(50) NULL;
    
    PRINT 'Added naming_convention column to clients table';
END
ELSE
BEGIN
    PRINT 'naming_convention column already exists in clients table';
END
GO

-- Add check constraint to ensure valid naming conventions
IF NOT EXISTS (
    SELECT * FROM sys.check_constraints 
    WHERE name = 'CK_Clients_NamingConvention'
)
BEGIN
    ALTER TABLE dbo.clients
    ADD CONSTRAINT CK_Clients_NamingConvention 
    CHECK (naming_convention IN ('AWS', 'SINSW', NULL));
    
    PRINT 'Added naming_convention check constraint to clients table';
END
ELSE
BEGIN
    PRINT 'Naming convention check constraint already exists';
END
GO

-- Update existing clients if needed (optional - update as required)
-- UPDATE dbo.clients SET naming_convention = 'AWS' WHERE client_name LIKE '%AWS%';
-- UPDATE dbo.clients SET naming_convention = 'SINSW' WHERE client_name LIKE '%SINSW%' OR client_name LIKE '%Infrastructure NSW%';
-- GO

PRINT 'Migration completed: add_naming_convention_to_clients.sql';
