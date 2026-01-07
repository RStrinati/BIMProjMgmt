-- ============================================================================
-- ETL Procedure: warehouse.usp_load_fact_coordinate_alignment_daily
-- Description: Load coordinate alignment snapshots into fact table
-- Dependencies: fact.coordinate_alignment_daily, dim.revit_file,
--               RevitHealthCheckDB.dbo.vw_CoordinateAlignmentCheck
-- Author: System
-- Created: 2026-01-06
-- ============================================================================

USE ProjectManagement;
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'warehouse')
BEGIN
    EXEC('CREATE SCHEMA warehouse');
END
GO

IF OBJECT_ID('warehouse.usp_load_fact_coordinate_alignment_daily', 'P') IS NOT NULL
BEGIN
    DROP PROCEDURE warehouse.usp_load_fact_coordinate_alignment_daily;
END
GO

CREATE PROCEDURE warehouse.usp_load_fact_coordinate_alignment_daily
    @snapshot_date DATETIME2 = NULL,
    @batch_id UNIQUEIDENTIFIER = NULL,
    @debug BIT = 0
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @rows_inserted INT = 0;
    DECLARE @start_time DATETIME2 = SYSDATETIME();

    SET @snapshot_date = COALESCE(@snapshot_date, SYSDATETIME());
    SET @batch_id = COALESCE(@batch_id, NEWID());

    BEGIN TRY
        IF @debug = 1
            PRINT CONCAT('Starting coordinate alignment load at ', FORMAT(@start_time, 'yyyy-MM-dd HH:mm:ss'), ' (Batch: ', @batch_id, ')');

        TRUNCATE TABLE fact.coordinate_alignment_daily;

        INSERT INTO fact.coordinate_alignment_daily (
            snapshot_date,
            batch_id,
            project_key,
            file_name_key,
            control_file_key,
            health_check_id,
            project_name,
            model_file_name,
            control_file_name,
            discipline_full_name,
            model_zone_code,
            control_zone_code,
            control_is_primary,
            pbp_eastwest,
            pbp_northsouth,
            pbp_elevation,
            pbp_angle_true_north,
            survey_eastwest,
            survey_northsouth,
            survey_elevation,
            survey_angle_true_north,
            control_pbp_eastwest,
            control_pbp_northsouth,
            control_pbp_elevation,
            control_pbp_angle_true_north,
            control_survey_eastwest,
            control_survey_northsouth,
            control_survey_elevation,
            control_survey_angle_true_north,
            pbp_compliant,
            survey_compliant,
            is_compliant,
            source_system,
            source_view
        )
        SELECT
            @snapshot_date,
            @batch_id,
            ca.pm_project_id,
            df.revit_file_key,
            dfc.revit_file_key,
            ca.nId,
            ca.strExtractedProjectName,
            ca.ModelFileName,
            ca.ControlFileName,
            ca.discipline_full_name,
            ca.model_zone_code,
            ca.control_zone_code,
            ca.ControlIsPrimary,
            ca.PBP_EastWest,
            ca.PBP_NorthSouth,
            ca.PBP_Elevation,
            ca.PBP_AngleToTrueNorth_Degrees,
            ca.Survey_EastWest,
            ca.Survey_NorthSouth,
            ca.Survey_Elevation,
            ca.Survey_AngleToTrueNorth_Degrees,
            ca.Control_PBP_EW,
            ca.Control_PBP_NS,
            ca.Control_PBP_Elevation,
            ca.Control_PBP_Angle,
            ca.Control_Survey_EW,
            ca.Control_Survey_NS,
            ca.Control_Survey_Elevation,
            ca.Control_Survey_Angle,
            ca.Is_PBP_Compliant,
            ca.Is_Survey_Compliant,
            ca.Is_Compliant,
            'RevitHealthCheckDB',
            'vw_CoordinateAlignmentCheck'
        FROM RevitHealthCheckDB.dbo.vw_CoordinateAlignmentCheck ca
        LEFT JOIN dim.revit_file df
            ON ca.ModelFileName = df.file_name_bk AND df.current_flag = 1
        LEFT JOIN dim.revit_file dfc
            ON ca.ControlFileName = dfc.file_name_bk AND dfc.current_flag = 1;

        SET @rows_inserted = @@ROWCOUNT;

        IF @debug = 1
        BEGIN
            DECLARE @duration_seconds INT = DATEDIFF(SECOND, @start_time, SYSDATETIME());
            PRINT CONCAT('Loaded ', @rows_inserted, ' alignment rows in ', @duration_seconds, ' seconds (Batch: ', @batch_id, ')');
        END

        RETURN 0;
    END TRY
    BEGIN CATCH
        PRINT CONCAT('ERROR in coordinate alignment load: ', ERROR_MESSAGE());
        PRINT CONCAT('Error Line: ', ERROR_LINE());
        PRINT CONCAT('Error Procedure: ', ERROR_PROCEDURE());
        RETURN 1;
    END CATCH
END;
GO

