-- Phase 1B: Create ExpectedModels and ExpectedModelAliases tables
-- Database: ProjectManagement
-- Date: January 16, 2026
-- Purpose: Enable expected-first quality register workflow

USE ProjectManagement;
GO

-- ===================== Table 1: ExpectedModels =====================
-- Authoritative registry of expected Revit models for a project
-- Represents intended deliverables, manually created and maintained
-- Never-empty register: always exists even if no observed files

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ExpectedModels')
BEGIN
    CREATE TABLE dbo.ExpectedModels (
        expected_model_id INT PRIMARY KEY IDENTITY(1,1),
        project_id INT NOT NULL,
        expected_model_key NVARCHAR(100) NOT NULL,
        display_name NVARCHAR(255) NULL,
        discipline NVARCHAR(50) NULL,
        company_id INT NULL,
        is_required BIT NOT NULL DEFAULT 1,
        created_at DATETIME NOT NULL DEFAULT GETDATE(),
        updated_at DATETIME NOT NULL DEFAULT GETDATE(),
        
        -- Constraints
        CONSTRAINT FK_ExpectedModels_ProjectId 
            FOREIGN KEY (project_id) REFERENCES dbo.Projects(project_id),
        CONSTRAINT FK_ExpectedModels_CompanyId 
            FOREIGN KEY (company_id) REFERENCES dbo.clients(client_id),
        CONSTRAINT UQ_ExpectedModels_ProjectKey 
            UNIQUE (project_id, expected_model_key)
    );
    
    -- Indexes for query performance
    CREATE INDEX IX_ExpectedModels_ProjectId 
        ON dbo.ExpectedModels(project_id);
    
    PRINT '✅ Created table: dbo.ExpectedModels';
END
ELSE
    PRINT '⚠️ Table ExpectedModels already exists (skipping)';
GO

-- ===================== Table 2: ExpectedModelAliases =====================
-- Maps observed filenames/keys to expected models
-- Enables reconciliation without modifying observed data
-- Supports multiple alias patterns per expected model

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ExpectedModelAliases')
BEGIN
    CREATE TABLE dbo.ExpectedModelAliases (
        expected_model_alias_id INT PRIMARY KEY IDENTITY(1,1),
        expected_model_id INT NOT NULL,
        project_id INT NULL,
        alias_pattern NVARCHAR(255) NOT NULL,
        match_type NVARCHAR(50) NOT NULL DEFAULT 'exact',  -- exact, contains, regex
        target_field NVARCHAR(50) NOT NULL DEFAULT 'filename',  -- filename, rvt_model_key
        is_active BIT NOT NULL DEFAULT 1,
        created_at DATETIME NOT NULL DEFAULT GETDATE(),
        
        -- Constraints
        CONSTRAINT FK_ExpectedModelAliases_ExpectedModelId 
            FOREIGN KEY (expected_model_id) REFERENCES dbo.ExpectedModels(expected_model_id),
        CONSTRAINT FK_ExpectedModelAliases_ProjectId 
            FOREIGN KEY (project_id) REFERENCES dbo.Projects(project_id),
        CONSTRAINT CK_ExpectedModelAliases_MatchType 
            CHECK (match_type IN ('exact', 'contains', 'regex')),
        CONSTRAINT CK_ExpectedModelAliases_TargetField 
            CHECK (target_field IN ('filename', 'rvt_model_key'))
    );
    
    -- Indexes for query performance
    CREATE INDEX IX_ExpectedModelAliases_ProjectActive 
        ON dbo.ExpectedModelAliases(project_id, is_active);
    CREATE INDEX IX_ExpectedModelAliases_ExpectedModelId 
        ON dbo.ExpectedModelAliases(expected_model_id);
    
    PRINT '✅ Created table: dbo.ExpectedModelAliases';
END
ELSE
    PRINT '⚠️ Table ExpectedModelAliases already exists (skipping)';
GO

-- ===================== Verification =====================
-- Check tables exist and show structure
IF OBJECT_ID('dbo.ExpectedModels', 'U') IS NOT NULL
BEGIN
    PRINT '';
    PRINT '=== ExpectedModels Structure ===';
    EXEC sp_help 'dbo.ExpectedModels';
END
GO

IF OBJECT_ID('dbo.ExpectedModelAliases', 'U') IS NOT NULL
BEGIN
    PRINT '';
    PRINT '=== ExpectedModelAliases Structure ===';
    EXEC sp_help 'dbo.ExpectedModelAliases';
END
GO

PRINT '';
PRINT '✅ Phase 1B: Table creation complete';
PRINT '';
PRINT 'Next steps:';
PRINT '1. Run check_schema.py to verify schema constants match DB structure';
PRINT '2. Implement Phase 1C: Update get_model_register() for mode=expected';
PRINT '3. Create Phase 1E endpoints: CRUD for expected models and aliases';
