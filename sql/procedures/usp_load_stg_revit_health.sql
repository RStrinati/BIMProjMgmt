-- =============================================
-- ETL Procedure: warehouse.usp_load_stg_revit_health
-- Description: Load staging table from RevitHealthCheckDB warehouse view
-- Dependencies: stg.revit_health_snapshots, RevitHealthCheckDB.dbo.vw_RevitHealthWarehouse_CrossDB
-- Author: Data Warehouse Team
-- Date: 2025-12-04
-- =============================================

USE ProjectManagement;
GO

-- Create schema if not exists
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'warehouse')
BEGIN
    EXEC('CREATE SCHEMA warehouse');
    PRINT 'Created schema: warehouse';
END
GO

-- Drop existing procedure
IF OBJECT_ID('warehouse.usp_load_stg_revit_health', 'P') IS NOT NULL
BEGIN
    DROP PROCEDURE warehouse.usp_load_stg_revit_health;
    PRINT 'Dropped existing procedure: warehouse.usp_load_stg_revit_health';
END
GO

CREATE PROCEDURE warehouse.usp_load_stg_revit_health
    @snapshot_date DATETIME2 = NULL,
    @batch_id UNIQUEIDENTIFIER = NULL,
    @debug BIT = 0
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    
    -- Variables
    DECLARE @rows_loaded INT = 0;
    DECLARE @start_time DATETIME2 = SYSDATETIME();
    DECLARE @error_message NVARCHAR(4000);
    
    -- Set defaults
    SET @snapshot_date = COALESCE(@snapshot_date, SYSDATETIME());
    SET @batch_id = COALESCE(@batch_id, NEWID());
    
    BEGIN TRY
        -- Log start
        IF @debug = 1
            PRINT CONCAT('Starting staging load at ', FORMAT(@start_time, 'yyyy-MM-dd HH:mm:ss'), ' (Batch: ', @batch_id, ')');
        
        -- Truncate staging table (full refresh pattern)
        TRUNCATE TABLE stg.revit_health_snapshots;
        
        IF @debug = 1
            PRINT 'Truncated staging table';
        
        -- Load from cross-database warehouse view
        INSERT INTO stg.revit_health_snapshots (
            health_check_id,
            revit_file_name,
            project_id,
            health_score,
            health_category,
            total_warnings,
            critical_warnings,
            file_size_mb,
            total_elements,
            family_count,
            revit_links,
            dwg_imports,
            dwg_links,
            total_views,
            views_not_on_sheets,
            view_efficiency_pct,
            naming_status,
            discipline_code,
            model_functional_code,
            control_is_primary,
            zone_code,
            link_health_flag,
            export_date,
            days_since_export,
            data_freshness,
            snapshot_date,
            batch_id,
            source_system,
            source_view
        )
        SELECT 
            wh.health_check_id,
            wh.revit_file_name,
            wh.pm_project_id,
            wh.calculated_health_score,
            wh.health_category,
            wh.total_warnings,
            wh.critical_warnings,
            wh.file_size_mb,
            wh.total_elements,
            wh.family_count,
            wh.revit_links,
            wh.dwg_imports,
            wh.dwg_links,
            wh.total_views,
            wh.views_not_on_sheets,
            wh.view_efficiency_pct,
            wh.validation_status,
            wh.discipline_code,
            wh.model_functional_code,
            wh.control_is_primary,
            wh.zone_code,
            wh.link_health_flag,
            wh.export_date,
            wh.days_since_export,
            wh.data_freshness,
            @snapshot_date,
            @batch_id,
            'RevitHealthCheckDB',
            'vw_RevitHealthWarehouse_CrossDB'
        FROM RevitHealthCheckDB.dbo.vw_RevitHealthWarehouse_CrossDB wh
        WHERE wh.mapping_status = 'Mapped'  -- Only load mapped files
          AND wh.health_check_id IS NOT NULL;
        
        SET @rows_loaded = @@ROWCOUNT;
        
        -- Log completion
        DECLARE @duration_seconds INT = DATEDIFF(SECOND, @start_time, SYSDATETIME());
        
        PRINT CONCAT(
            'Successfully loaded ', @rows_loaded, ' health snapshots ',
            'in ', @duration_seconds, ' seconds ',
            '(Batch: ', @batch_id, ')'
        );
        
        IF @debug = 1
        BEGIN
            -- Show sample of loaded data
            SELECT TOP 5
                snapshot_id,
                health_check_id,
                revit_file_name,
                project_id,
                health_score,
                health_category,
                total_warnings,
                export_date,
                loaded_at
            FROM stg.revit_health_snapshots
            ORDER BY health_score ASC;
            
            -- Show summary statistics
            SELECT 
                COUNT(*) as total_rows,
                COUNT(DISTINCT project_id) as distinct_projects,
                COUNT(DISTINCT revit_file_name) as distinct_files,
                AVG(health_score) as avg_health_score,
                MIN(health_score) as min_health_score,
                MAX(health_score) as max_health_score,
                SUM(total_warnings) as total_warnings,
                MIN(export_date) as earliest_export,
                MAX(export_date) as latest_export
            FROM stg.revit_health_snapshots;
        END
        
        -- Return success code
        RETURN 0;
        
    END TRY
    BEGIN CATCH
        SET @error_message = ERROR_MESSAGE();
        
        PRINT CONCAT('ERROR in staging load: ', @error_message);
        PRINT CONCAT('Error Line: ', ERROR_LINE());
        PRINT CONCAT('Error Procedure: ', ERROR_PROCEDURE());
        
        -- Return error code
        RETURN 1;
    END CATCH
END;
GO

-- Add procedure description
EXEC sys.sp_addextendedproperty 
    @name=N'MS_Description', 
    @value=N'ETL procedure to load Revit health snapshots from RevitHealthCheckDB warehouse view into staging table. Uses truncate/reload pattern. Only loads mapped files.', 
    @level0type=N'SCHEMA', @level0name=N'warehouse', 
    @level1type=N'PROCEDURE', @level1name=N'usp_load_stg_revit_health';
GO

PRINT 'Successfully created procedure: warehouse.usp_load_stg_revit_health';
GO

-- Test the procedure (optional)
-- EXEC warehouse.usp_load_stg_revit_health @debug = 1;
