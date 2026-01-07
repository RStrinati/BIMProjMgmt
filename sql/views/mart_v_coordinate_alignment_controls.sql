-- ============================================================================
-- View: mart.v_coordinate_alignment_controls
-- Purpose: Control model coordinate alignment summary for dashboard tables
-- Author: System
-- Created: 2026-01-06
-- ============================================================================

USE ProjectManagement;
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'mart')
BEGIN
    EXEC('CREATE SCHEMA mart');
END
GO

IF OBJECT_ID('mart.v_coordinate_alignment_controls', 'V') IS NOT NULL
    DROP VIEW mart.v_coordinate_alignment_controls;
GO

CREATE VIEW mart.v_coordinate_alignment_controls AS
WITH Latest AS (
    SELECT
        alignment_id,
        ROW_NUMBER() OVER (
            PARTITION BY project_key, control_file_name, control_zone_code
            ORDER BY snapshot_date DESC, alignment_id DESC
        ) AS rn
    FROM fact.coordinate_alignment_daily
    WHERE control_file_name IS NOT NULL
)
SELECT
    f.project_key AS pm_project_id,
    f.project_name,
    f.control_file_name,
    f.control_zone_code,
    f.control_is_primary,
    f.control_pbp_eastwest,
    f.control_pbp_northsouth,
    f.control_pbp_elevation,
    f.control_pbp_angle_true_north,
    f.control_survey_eastwest,
    f.control_survey_northsouth,
    f.control_survey_elevation,
    f.control_survey_angle_true_north,
    f.snapshot_date
FROM fact.coordinate_alignment_daily f
INNER JOIN Latest l ON f.alignment_id = l.alignment_id
WHERE l.rn = 1;
GO

