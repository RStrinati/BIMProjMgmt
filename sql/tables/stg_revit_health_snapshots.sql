-- =============================================
-- Staging Table: stg.revit_health_snapshots
-- Description: Landing zone for Revit health check data from warehouse view
-- Dependencies: None (staging layer)
-- Author: Data Warehouse Team
-- Date: 2025-12-04
-- =============================================

USE ProjectManagement;
GO

-- Create schema if not exists
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'stg')
BEGIN
    EXEC('CREATE SCHEMA stg');
    PRINT 'Created schema: stg';
END
GO

-- Drop existing table if exists (for development only)
IF OBJECT_ID('stg.revit_health_snapshots', 'U') IS NOT NULL
BEGIN
    DROP TABLE stg.revit_health_snapshots;
    PRINT 'Dropped existing table: stg.revit_health_snapshots';
END
GO

-- Create staging table
CREATE TABLE stg.revit_health_snapshots (
    -- Staging surrogate key
    snapshot_id INT IDENTITY(1,1) NOT NULL,
    
    -- Source system references
    health_check_id INT NOT NULL,
    revit_file_name NVARCHAR(510) NOT NULL,
    project_id INT NULL,  -- FK to Projects table
    
    -- Health metrics
    health_score INT NULL,
    health_category VARCHAR(20) NULL,
    total_warnings INT NULL,
    critical_warnings INT NULL,
    
    -- File metrics
    file_size_mb DECIMAL(10,2) NULL,
    total_elements INT NULL,
    family_count INT NULL,
    revit_links INT NULL,
    dwg_imports INT NULL,
    dwg_links INT NULL,
    
    -- View metrics
    total_views INT NULL,
    views_not_on_sheets INT NULL,
    view_efficiency_pct DECIMAL(5,2) NULL,
    
    -- Validation status
    naming_status VARCHAR(20) NULL,
    discipline_code VARCHAR(10) NULL,
    model_functional_code VARCHAR(10) NULL,
    
    -- Control model indicators
    control_is_primary BIT NULL,
    zone_code VARCHAR(10) NULL,
    
    -- Link health
    link_health_flag VARCHAR(50) NULL,
    
    -- Temporal attributes
    export_date DATETIME2 NULL,
    days_since_export INT NULL,
    data_freshness VARCHAR(20) NULL,
    snapshot_date DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    
    -- ETL metadata
    loaded_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    source_system VARCHAR(50) DEFAULT 'RevitHealthCheckDB',
    source_view VARCHAR(100) DEFAULT 'vw_RevitHealthWarehouse_CrossDB',
    batch_id UNIQUEIDENTIFIER DEFAULT NEWID(),
    
    -- Error tracking
    has_error BIT DEFAULT 0,
    error_message NVARCHAR(500) NULL,
    
    -- Primary key
    CONSTRAINT PK_stg_revit_health_snapshots PRIMARY KEY CLUSTERED (snapshot_id)
);
GO

-- Indexes for ETL performance
CREATE NONCLUSTERED INDEX IX_stg_revit_health_project_export 
    ON stg.revit_health_snapshots(project_id, export_date)
    INCLUDE (health_check_id, health_score);
GO

CREATE NONCLUSTERED INDEX IX_stg_revit_health_file 
    ON stg.revit_health_snapshots(revit_file_name, export_date);
GO

CREATE NONCLUSTERED INDEX IX_stg_revit_health_check_id 
    ON stg.revit_health_snapshots(health_check_id);
GO

CREATE NONCLUSTERED INDEX IX_stg_revit_health_batch 
    ON stg.revit_health_snapshots(batch_id, loaded_at);
GO

-- Add table description
EXEC sys.sp_addextendedproperty 
    @name=N'MS_Description', 
    @value=N'Staging table for Revit health check snapshots loaded from RevitHealthCheckDB warehouse view. Truncate and reload pattern used for ETL.', 
    @level0type=N'SCHEMA', @level0name=N'stg', 
    @level1type=N'TABLE',  @level1name=N'revit_health_snapshots';
GO

-- Add key column descriptions
EXEC sys.sp_addextendedproperty 
    @name=N'MS_Description', @value=N'Staging surrogate key, resets on each load', 
    @level0type=N'SCHEMA', @level0name=N'stg', 
    @level1type=N'TABLE', @level1name=N'revit_health_snapshots',
    @level2type=N'COLUMN', @level2name=N'snapshot_id';

EXEC sys.sp_addextendedproperty 
    @name=N'MS_Description', @value=N'Source system primary key from RevitHealthCheckDB', 
    @level0type=N'SCHEMA', @level0name=N'stg', 
    @level1type=N'TABLE', @level1name=N'revit_health_snapshots',
    @level2type=N'COLUMN', @level2name=N'health_check_id';

EXEC sys.sp_addextendedproperty 
    @name=N'MS_Description', @value=N'Unique identifier for this ETL batch run', 
    @level0type=N'SCHEMA', @level0name=N'stg', 
    @level1type=N'TABLE', @level1name=N'revit_health_snapshots',
    @level2type=N'COLUMN', @level2name=N'batch_id';
GO

PRINT 'Successfully created table: stg.revit_health_snapshots';
PRINT 'Created indexes: IX_stg_revit_health_project_export, IX_stg_revit_health_file, IX_stg_revit_health_check_id, IX_stg_revit_health_batch';
GO
