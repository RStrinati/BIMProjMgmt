-- =============================================
-- Dimension Table: dim.revit_file
-- Description: SCD Type 2 dimension for Revit file metadata
-- Dependencies: None (base dimension)
-- Author: Data Warehouse Team
-- Date: 2025-12-04
-- =============================================

USE ProjectManagement;
GO

-- Create schema if not exists
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'dim')
BEGIN
    EXEC('CREATE SCHEMA dim');
    PRINT 'Created schema: dim';
END
GO

-- Drop existing table if exists (for development only)
IF OBJECT_ID('dim.revit_file', 'U') IS NOT NULL
BEGIN
    DROP TABLE dim.revit_file;
    PRINT 'Dropped existing table: dim.revit_file';
END
GO

-- Create dimension table
CREATE TABLE dim.revit_file (
    -- Surrogate key
    revit_file_key INT IDENTITY(1,1) NOT NULL,
    
    -- Business key (natural key from source)
    file_name_bk NVARCHAR(510) NOT NULL,
    
    -- File naming attributes
    normalized_file_name NVARCHAR(510) NULL,
    discipline_code VARCHAR(10) NULL,
    discipline_full_name VARCHAR(100) NULL,
    project_number VARCHAR(50) NULL,
    
    -- Classification attributes
    model_functional_code VARCHAR(10) NULL,
    is_control_model BIT DEFAULT 0,
    zone_code VARCHAR(10) NULL,
    
    -- Validation status
    naming_status VARCHAR(20) NULL,  -- Valid, Invalid, Warning
    validation_reason NVARCHAR(500) NULL,
    
    -- File metadata
    file_extension VARCHAR(10) NULL,
    file_category VARCHAR(50) NULL,  -- Model, Family, Template
    
    -- SCD Type 2 tracking
    valid_from DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    valid_to DATETIME2 NOT NULL DEFAULT '9999-12-31 23:59:59.9999999',
    current_flag BIT NOT NULL DEFAULT 1,
    
    -- Audit columns
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    updated_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    created_by VARCHAR(100) DEFAULT SYSTEM_USER,
    updated_by VARCHAR(100) DEFAULT SYSTEM_USER,
    
    -- Primary key
    CONSTRAINT PK_dim_revit_file PRIMARY KEY CLUSTERED (revit_file_key)
);
GO

-- Indexes for performance
CREATE UNIQUE NONCLUSTERED INDEX IX_dim_revit_file_bk_current 
    ON dim.revit_file(file_name_bk) 
    WHERE current_flag = 1;
GO

CREATE NONCLUSTERED INDEX IX_dim_revit_file_discipline 
    ON dim.revit_file(discipline_code)
    INCLUDE (discipline_full_name, current_flag);
GO

CREATE NONCLUSTERED INDEX IX_dim_revit_file_project_number 
    ON dim.revit_file(project_number)
    WHERE current_flag = 1;
GO

CREATE NONCLUSTERED INDEX IX_dim_revit_file_validation 
    ON dim.revit_file(naming_status, current_flag);
GO

-- Add table description
EXEC sys.sp_addextendedproperty 
    @name=N'MS_Description', 
    @value=N'Dimension table for Revit file metadata with SCD Type 2 tracking for historical changes in naming conventions and validation status', 
    @level0type=N'SCHEMA', @level0name=N'dim', 
    @level1type=N'TABLE',  @level1name=N'revit_file';
GO

-- Add column descriptions
EXEC sys.sp_addextendedproperty 
    @name=N'MS_Description', @value=N'Surrogate key for dimension', 
    @level0type=N'SCHEMA', @level0name=N'dim', 
    @level1type=N'TABLE', @level1name=N'revit_file',
    @level2type=N'COLUMN', @level2name=N'revit_file_key';

EXEC sys.sp_addextendedproperty 
    @name=N'MS_Description', @value=N'Natural key - original Revit file name from source system', 
    @level0type=N'SCHEMA', @level0name=N'dim', 
    @level1type=N'TABLE', @level1name=N'revit_file',
    @level2type=N'COLUMN', @level2name=N'file_name_bk';

EXEC sys.sp_addextendedproperty 
    @name=N'MS_Description', @value=N'1=Current version, 0=Historical version (SCD Type 2)', 
    @level0type=N'SCHEMA', @level0name=N'dim', 
    @level1type=N'TABLE', @level1name=N'revit_file',
    @level2type=N'COLUMN', @level2name=N'current_flag';
GO

PRINT 'Successfully created table: dim.revit_file';
PRINT 'Created indexes: IX_dim_revit_file_bk_current, IX_dim_revit_file_discipline, IX_dim_revit_file_project_number, IX_dim_revit_file_validation';
GO
