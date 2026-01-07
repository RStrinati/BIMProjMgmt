-- ============================================================================
-- Table: fact.coordinate_alignment_daily
-- Purpose: Snapshot of coordinate alignment for Revit files (PBP + Survey)
-- Author: System
-- Created: 2026-01-06
-- ============================================================================

USE ProjectManagement;
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'fact')
BEGIN
    EXEC('CREATE SCHEMA fact');
END
GO

IF OBJECT_ID('fact.coordinate_alignment_daily', 'U') IS NOT NULL
BEGIN
    DROP TABLE fact.coordinate_alignment_daily;
END
GO

CREATE TABLE fact.coordinate_alignment_daily (
    alignment_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    snapshot_date DATETIME2 NOT NULL,
    batch_id UNIQUEIDENTIFIER NOT NULL,

    project_key INT NULL,
    file_name_key INT NULL,
    control_file_key INT NULL,
    health_check_id INT NULL,

    project_name NVARCHAR(255) NULL,
    model_file_name NVARCHAR(255) NULL,
    control_file_name NVARCHAR(255) NULL,
    discipline_full_name NVARCHAR(255) NULL,
    model_zone_code NVARCHAR(50) NULL,
    control_zone_code NVARCHAR(50) NULL,
    control_is_primary BIT NULL,

    -- Model base point
    pbp_eastwest FLOAT NULL,
    pbp_northsouth FLOAT NULL,
    pbp_elevation FLOAT NULL,
    pbp_angle_true_north FLOAT NULL,

    -- Model survey point
    survey_eastwest FLOAT NULL,
    survey_northsouth FLOAT NULL,
    survey_elevation FLOAT NULL,
    survey_angle_true_north FLOAT NULL,

    -- Control base point
    control_pbp_eastwest FLOAT NULL,
    control_pbp_northsouth FLOAT NULL,
    control_pbp_elevation FLOAT NULL,
    control_pbp_angle_true_north FLOAT NULL,

    -- Control survey point
    control_survey_eastwest FLOAT NULL,
    control_survey_northsouth FLOAT NULL,
    control_survey_elevation FLOAT NULL,
    control_survey_angle_true_north FLOAT NULL,

    pbp_compliant BIT NULL,
    survey_compliant BIT NULL,
    is_compliant BIT NULL,

    source_system NVARCHAR(100) NOT NULL DEFAULT 'RevitHealthCheckDB',
    source_view NVARCHAR(200) NOT NULL DEFAULT 'vw_CoordinateAlignmentCheck',
    loaded_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO

CREATE NONCLUSTERED INDEX IX_fact_coordinate_alignment_project
    ON fact.coordinate_alignment_daily(project_key, snapshot_date);
GO

CREATE NONCLUSTERED INDEX IX_fact_coordinate_alignment_file
    ON fact.coordinate_alignment_daily(file_name_key, control_file_key);
GO

CREATE NONCLUSTERED INDEX IX_fact_coordinate_alignment_project_model
    ON fact.coordinate_alignment_daily(project_key, model_file_name)
    INCLUDE (control_file_name, discipline_full_name, model_zone_code, control_zone_code, control_is_primary, pbp_eastwest, pbp_northsouth, pbp_elevation, pbp_angle_true_north, survey_eastwest, survey_northsouth, survey_elevation, survey_angle_true_north, pbp_compliant, survey_compliant, is_compliant, snapshot_date);
GO

CREATE NONCLUSTERED INDEX IX_fact_coordinate_alignment_project_control
    ON fact.coordinate_alignment_daily(project_key, control_file_name, control_zone_code)
    INCLUDE (control_is_primary, control_pbp_eastwest, control_pbp_northsouth, control_pbp_elevation, control_pbp_angle_true_north, control_survey_eastwest, control_survey_northsouth, control_survey_elevation, control_survey_angle_true_north, snapshot_date);
GO
