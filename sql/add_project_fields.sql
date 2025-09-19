-- Add missing columns to projects table for enhanced project creation
-- This script adds fields collected by the UI dialog that are missing from the database

USE ProjectManagement;
GO

-- Add project type reference
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('projects') AND name = 'type_id')
BEGIN
    ALTER TABLE projects ADD type_id INT NULL;
    PRINT 'Added type_id column to projects table';
END

-- Add area/capacity fields
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('projects') AND name = 'area_hectares')
BEGIN
    ALTER TABLE projects ADD area_hectares DECIMAL(10,2) NULL;
    PRINT 'Added area_hectares column to projects table';
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('projects') AND name = 'mw_capacity')
BEGIN
    ALTER TABLE projects ADD mw_capacity DECIMAL(10,2) NULL;
    PRINT 'Added mw_capacity column to projects table';
END

-- Add location fields
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('projects') AND name = 'address')
BEGIN
    ALTER TABLE projects ADD address NVARCHAR(500) NULL;
    PRINT 'Added address column to projects table';
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('projects') AND name = 'city')
BEGIN
    ALTER TABLE projects ADD city NVARCHAR(200) NULL;
    PRINT 'Added city column to projects table';
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('projects') AND name = 'state')
BEGIN
    ALTER TABLE projects ADD state NVARCHAR(200) NULL;
    PRINT 'Added state column to projects table';
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('projects') AND name = 'postcode')
BEGIN
    ALTER TABLE projects ADD postcode NVARCHAR(20) NULL;
    PRINT 'Added postcode column to projects table';
END

-- Add other potentially useful fields from constants
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('projects') AND name = 'client_id')
BEGIN
    ALTER TABLE projects ADD client_id INT NULL;
    PRINT 'Added client_id column to projects table';
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('projects') AND name = 'sector_id')
BEGIN
    ALTER TABLE projects ADD sector_id INT NULL;
    PRINT 'Added sector_id column to projects table';
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('projects') AND name = 'method_id')
BEGIN
    ALTER TABLE projects ADD method_id INT NULL;
    PRINT 'Added method_id column to projects table';
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('projects') AND name = 'phase_id')
BEGIN
    ALTER TABLE projects ADD phase_id INT NULL;
    PRINT 'Added phase_id column to projects table';
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('projects') AND name = 'stage_id')
BEGIN
    ALTER TABLE projects ADD stage_id INT NULL;
    PRINT 'Added stage_id column to projects table';
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('projects') AND name = 'project_manager')
BEGIN
    ALTER TABLE projects ADD project_manager INT NULL;
    PRINT 'Added project_manager column to projects table';
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('projects') AND name = 'internal_lead')
BEGIN
    ALTER TABLE projects ADD internal_lead INT NULL;
    PRINT 'Added internal_lead column to projects table';
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('projects') AND name = 'contract_number')
BEGIN
    ALTER TABLE projects ADD contract_number NVARCHAR(100) NULL;
    PRINT 'Added contract_number column to projects table';
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('projects') AND name = 'contract_value')
BEGIN
    ALTER TABLE projects ADD contract_value DECIMAL(15,2) NULL;
    PRINT 'Added contract_value column to projects table';
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('projects') AND name = 'agreed_fee')
BEGIN
    ALTER TABLE projects ADD agreed_fee DECIMAL(15,2) NULL;
    PRINT 'Added agreed_fee column to projects table';
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('projects') AND name = 'payment_terms')
BEGIN
    ALTER TABLE projects ADD payment_terms NVARCHAR(1000) NULL;
    PRINT 'Added payment_terms column to projects table';
END

PRINT 'Database schema update completed successfully!';
GO