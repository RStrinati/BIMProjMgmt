-- =============================================
-- Fact Table: fact.revit_health_daily
-- Description: Daily snapshot fact table for Revit model health metrics
-- Dependencies: dim.revit_file (mandatory); dim.project/dim.date optional when enforced via FKs
-- Author: Data Warehouse Team
-- Date: 2025-12-04
-- =============================================

USE ProjectManagement;
GO

-- Create schema if not exists
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'fact')
BEGIN
    EXEC('CREATE SCHEMA fact');
    PRINT 'Created schema: fact';
END
GO

-- Drop existing table if exists (for development only)
IF OBJECT_ID('fact.revit_health_daily', 'U') IS NOT NULL
BEGIN
    DROP TABLE fact.revit_health_daily;
    PRINT 'Dropped existing table: fact.revit_health_daily';
END
GO

-- Create fact table
CREATE TABLE fact.revit_health_daily (
    -- Fact surrogate key
    health_fact_id BIGINT IDENTITY(1,1) NOT NULL,
    
    -- Dimensional keys (foreign keys)
    date_key INT NOT NULL,  -- FK to dim.date
    project_key INT NULL,  -- FK to dim.project (nullable for unmapped files)
    file_name_key INT NOT NULL,  -- FK to dim.revit_file
    
    -- Degenerate dimensions (source system keys)
    health_check_id INT NOT NULL,
    model_functional_code VARCHAR(10) NULL,
    
    -- Health measures
    health_score INT NULL,
    health_category VARCHAR(20) NULL,
    total_warnings INT NULL,
    critical_warnings INT NULL,
    
    -- File size measures
    file_size_mb DECIMAL(10,2) NULL,
    file_size_category VARCHAR(20) NULL,  -- Small, Medium, Large, Very Large
    
    -- Element measures
    total_elements INT NULL,
    family_count INT NULL,
    
    -- View measures
    total_views INT NULL,
    views_not_on_sheets INT NULL,
    view_efficiency_pct DECIMAL(5,2) NULL,
    
    -- Link health measures
    revit_links INT NULL,
    dwg_imports INT NULL,
    dwg_links INT NULL,
    link_health_flag VARCHAR(50) NULL,
    
    -- Validation flags (boolean measures)
    naming_valid BIT NULL,
    coordinates_aligned BIT NULL,
    grids_aligned BIT NULL,
    levels_aligned BIT NULL,
    
    -- Control model indicators
    is_control_model BIT DEFAULT 0,
    zone_code VARCHAR(10) NULL,
    
    -- Temporal measures
    export_datetime DATETIME2 NULL,
    days_since_export INT NULL,
    data_freshness VARCHAR(20) NULL,  -- Current, Recent, Stale, Very Stale
    
    -- Calculated measures
    warnings_per_1000_elements DECIMAL(10,2) NULL,
    critical_warning_ratio DECIMAL(5,4) NULL,
    
    -- ETL metadata
    loaded_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    batch_id UNIQUEIDENTIFIER NULL,
    source_system VARCHAR(50) DEFAULT 'RevitHealthCheckDB',
    
    -- Primary key
    CONSTRAINT PK_fact_revit_health_daily PRIMARY KEY NONCLUSTERED (health_fact_id)
);
GO

-- Clustered index on date for time-series queries (partition key)
CREATE CLUSTERED INDEX IX_fact_revit_health_date_project 
    ON fact.revit_health_daily(date_key, project_key);
GO

-- Additional indexes for common query patterns
CREATE NONCLUSTERED INDEX IX_fact_revit_health_project_file 
    ON fact.revit_health_daily(project_key, file_name_key)
    INCLUDE (health_score, health_category, total_warnings);
GO

CREATE NONCLUSTERED INDEX IX_fact_revit_health_score 
    ON fact.revit_health_daily(health_score, health_category)
    INCLUDE (project_key, date_key);
GO

CREATE NONCLUSTERED INDEX IX_fact_revit_health_check_id 
    ON fact.revit_health_daily(health_check_id)
    INCLUDE (health_fact_id);
GO

CREATE NONCLUSTERED INDEX IX_fact_revit_health_validation 
    ON fact.revit_health_daily(naming_valid, coordinates_aligned, grids_aligned, levels_aligned);
GO

CREATE NONCLUSTERED INDEX IX_fact_revit_health_control_model 
    ON fact.revit_health_daily(is_control_model, project_key)
    WHERE is_control_model = 1;
GO

-- Foreign key constraints (commented out for initial load - can be enabled later)
-- ALTER TABLE fact.revit_health_daily
--     ADD CONSTRAINT FK_fact_revit_health_date 
--     FOREIGN KEY (date_key) REFERENCES dim.date(date_key);
-- 
-- ALTER TABLE fact.revit_health_daily
--     ADD CONSTRAINT FK_fact_revit_health_project 
--     FOREIGN KEY (project_key) REFERENCES dim.project(project_key);
-- 
-- ALTER TABLE fact.revit_health_daily
--     ADD CONSTRAINT FK_fact_revit_health_file 
--     FOREIGN KEY (file_name_key) REFERENCES dim.revit_file(revit_file_key);
-- GO

-- Add table description
EXEC sys.sp_addextendedproperty 
    @name=N'MS_Description', 
    @value=N'Daily snapshot fact table capturing Revit model health metrics. One row per health check per file per day. Supports historical trend analysis.', 
    @level0type=N'SCHEMA', @level0name=N'fact', 
    @level1type=N'TABLE',  @level1name=N'revit_health_daily';
GO

-- Add key column descriptions
EXEC sys.sp_addextendedproperty 
    @name=N'MS_Description', @value=N'Fact table surrogate key', 
    @level0type=N'SCHEMA', @level0name=N'fact', 
    @level1type=N'TABLE', @level1name=N'revit_health_daily',
    @level2type=N'COLUMN', @level2name=N'health_fact_id';

EXEC sys.sp_addextendedproperty 
    @name=N'MS_Description', @value=N'Foreign key to dim.date (date of health check export)', 
    @level0type=N'SCHEMA', @level0name=N'fact', 
    @level1type=N'TABLE', @level1name=N'revit_health_daily',
    @level2type=N'COLUMN', @level2name=N'date_key';

EXEC sys.sp_addextendedproperty 
    @name=N'MS_Description', @value=N'Foreign key to dim.project (nullable for unmapped files)', 
    @level0type=N'SCHEMA', @level0name=N'fact', 
    @level1type=N'TABLE', @level1name=N'revit_health_daily',
    @level2type=N'COLUMN', @level2name=N'project_key';

EXEC sys.sp_addextendedproperty 
    @name=N'MS_Description', @value=N'Foreign key to dim.revit_file', 
    @level0type=N'SCHEMA', @level0name=N'fact', 
    @level1type=N'TABLE', @level1name=N'revit_health_daily',
    @level2type=N'COLUMN', @level2name=N'file_name_key';

EXEC sys.sp_addextendedproperty 
    @name=N'MS_Description', @value=N'Calculated health score 0-100 based on warnings and file characteristics', 
    @level0type=N'SCHEMA', @level0name=N'fact', 
    @level1type=N'TABLE', @level1name=N'revit_health_daily',
    @level2type=N'COLUMN', @level2name=N'health_score';
GO

PRINT 'Successfully created table: fact.revit_health_daily';
PRINT 'Created indexes: IX_fact_revit_health_date_project (clustered), IX_fact_revit_health_project_file, IX_fact_revit_health_score, IX_fact_revit_health_check_id, IX_fact_revit_health_validation, IX_fact_revit_health_control_model';
GO
