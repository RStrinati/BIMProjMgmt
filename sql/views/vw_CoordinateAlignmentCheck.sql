-- ============================================================================
-- Master Coordinate Alignment View (RevitHealthCheckDB)
-- Purpose: Prefer AWS control model alignment logic, fall back to legacy logic
-- Author: System
-- Created: 2026-01-06
-- ============================================================================

USE RevitHealthCheckDB;
GO

IF OBJECT_ID('dbo.vw_CoordinateAlignmentCheck', 'V') IS NOT NULL
    DROP VIEW dbo.vw_CoordinateAlignmentCheck;
GO

CREATE VIEW dbo.vw_CoordinateAlignmentCheck AS
WITH AwsAlign AS (
    SELECT
        pm_project_id,
        rvt_model_key,
        nId,
        strExtractedProjectName,
        ModelFileName,
        model_zone_code,
        ControlFileName,
        control_zone_code,
        discipline_full_name,
        ControlIsPrimary,

        Survey_PosX, Survey_PosY, Survey_PosZ,
        Survey_EastWest, Survey_NorthSouth, Survey_Elevation,
        Survey_AngleToTrueNorth_Degrees,

        Control_Survey_PosX, Control_Survey_PosY, Control_Survey_PosZ,
        Control_Survey_EW, Control_Survey_NS, Control_Survey_Elevation,
        Control_Survey_Angle,

        Delta_Survey_X, Delta_Survey_Y, Delta_Survey_Z,
        Delta_Survey_EW, Delta_Survey_NS, Delta_Survey_Elev, Delta_Survey_Angle,

        PBP_PosX, PBP_PosY, PBP_PosZ,
        PBP_EastWest, PBP_NorthSouth, PBP_Elevation,
        PBP_AngleToTrueNorth_Degrees,

        Control_PBP_PosX, Control_PBP_PosY, Control_PBP_PosZ,
        Control_PBP_EW, Control_PBP_NS, Control_PBP_Elevation,
        Control_PBP_Angle,

        Delta_PBP_X, Delta_PBP_Y, Delta_PBP_Z,
        Delta_PBP_EW, Delta_PBP_NS, Delta_PBP_Elev, Delta_PBP_Angle,

        Is_Survey_Compliant,
        Survey_Compliance_Status,
        Is_PBP_Compliant,
        PBP_Compliance_Status,
        Is_Compliant
    FROM dbo.qry_CoordinateAlignmentCheckAWS
),
LegacyAlign AS (
    SELECT
        COALESCE(lf.pm_project_id, p.project_id) AS pm_project_id,
        CONCAT(CAST(COALESCE(lf.pm_project_id, p.project_id) AS varchar(20)), '|', COALESCE(lf.NormalizedFileName, l.ModelFileName)) AS rvt_model_key,
        l.nId,
        l.strExtractedProjectName,
        l.ModelFileName,
        CAST(NULL AS varchar(50)) AS model_zone_code,
        l.ControlFileName,
        CAST(NULL AS varchar(50)) AS control_zone_code,
        l.discipline_full_name,
        CAST(NULL AS bit) AS ControlIsPrimary,

        l.Survey_PosX, l.Survey_PosY, l.Survey_PosZ,
        l.Survey_EastWest, l.Survey_NorthSouth, l.Survey_Elevation,
        l.Survey_AngleToTrueNorth_Degrees,

        l.Control_Survey_PosX, l.Control_Survey_PosY, l.Control_Survey_PosZ,
        l.Control_Survey_EW, l.Control_Survey_NS, l.Control_Survey_Elevation,
        l.Control_Survey_Angle,

        ROUND(l.Survey_PosX - l.Control_Survey_PosX, 2) AS Delta_Survey_X,
        ROUND(l.Survey_PosY - l.Control_Survey_PosY, 2) AS Delta_Survey_Y,
        ROUND(l.Survey_PosZ - l.Control_Survey_PosZ, 2) AS Delta_Survey_Z,
        ROUND(l.Survey_EastWest - l.Control_Survey_EW, 2) AS Delta_Survey_EW,
        ROUND(l.Survey_NorthSouth - l.Control_Survey_NS, 2) AS Delta_Survey_NS,
        ROUND(l.Survey_Elevation - l.Control_Survey_Elevation, 2) AS Delta_Survey_Elev,
        ROUND(l.Survey_AngleToTrueNorth_Degrees - l.Control_Survey_Angle, 2) AS Delta_Survey_Angle,

        l.PBP_PosX, l.PBP_PosY, l.PBP_PosZ,
        l.PBP_EastWest, l.PBP_NorthSouth, l.PBP_Elevation,
        l.PBP_AngleToTrueNorth_Degrees,

        l.Control_PBP_PosX, l.Control_PBP_PosY, l.Control_PBP_PosZ,
        l.Control_PBP_EW, l.Control_PBP_NS, l.Control_PBP_Elevation,
        l.Control_PBP_Angle,

        ROUND(l.PBP_PosX - l.Control_PBP_PosX, 2) AS Delta_PBP_X,
        ROUND(l.PBP_PosY - l.Control_PBP_PosY, 2) AS Delta_PBP_Y,
        ROUND(l.PBP_PosZ - l.Control_PBP_PosZ, 2) AS Delta_PBP_Z,
        ROUND(l.PBP_EastWest - l.Control_PBP_EW, 2) AS Delta_PBP_EW,
        ROUND(l.PBP_NorthSouth - l.Control_PBP_NS, 2) AS Delta_PBP_NS,
        ROUND(l.PBP_Elevation - l.Control_PBP_Elevation, 2) AS Delta_PBP_Elev,
        ROUND(l.PBP_AngleToTrueNorth_Degrees - l.Control_PBP_Angle, 2) AS Delta_PBP_Angle,

        l.Is_Survey_Compliant,
        CASE
            WHEN l.Is_Survey_Compliant IS NULL THEN 'No control configured'
            WHEN l.Is_Survey_Compliant = 1 THEN 'Compliant'
            ELSE 'Non-Compliant'
        END AS Survey_Compliance_Status,
        l.Is_PBP_Compliant,
        CASE
            WHEN l.Is_PBP_Compliant IS NULL THEN 'No control configured'
            WHEN l.Is_PBP_Compliant = 1 THEN 'Compliant'
            ELSE 'Non-Compliant'
        END AS PBP_Compliance_Status,
        l.Is_Compliant
    FROM dbo.qry_CoordinateAlignmentCheck l
    LEFT JOIN dbo.vw_LatestRvtFiles lf
        ON l.nId = lf.nId
    LEFT JOIN ProjectManagement.dbo.projects p
        ON l.strExtractedProjectName = p.project_name
)
SELECT *
FROM AwsAlign
WHERE ControlFileName IS NOT NULL

UNION ALL

SELECT *
FROM LegacyAlign
WHERE ControlFileName IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM AwsAlign a
      WHERE a.nId = LegacyAlign.nId
        AND a.ControlFileName IS NOT NULL
  )

UNION ALL

SELECT *
FROM AwsAlign
WHERE ControlFileName IS NULL
  AND NOT EXISTS (
      SELECT 1
      FROM LegacyAlign l
      WHERE l.nId = AwsAlign.nId
        AND l.ControlFileName IS NOT NULL
  );
GO

