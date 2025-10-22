-- =====================================================================
-- Enhanced Deconstructed Views with Project Context
-- Combines existing JSON shredding views with project mapping
-- Author: System
-- Created: 2025-10-16
-- =====================================================================

USE RevitHealthCheckDB;
GO

-- =====================================================================
-- Revit Grids with Project Context
-- =====================================================================

IF OBJECT_ID('dbo.vw_RevitHealth_GridsWithProjects', 'V') IS NOT NULL
    DROP VIEW dbo.vw_RevitHealth_GridsWithProjects;
GO

CREATE VIEW dbo.vw_RevitHealth_GridsWithProjects AS
SELECT
    wh.pm_project_id,
    wh.pm_project_name,
    wh.project_status,
    wh.client_name,
    wh.health_check_id,
    wh.revit_file_name,
    wh.export_date,
    g.*
FROM dbo.vw_RevitHealthWarehouse_CrossDB wh
INNER JOIN dbo.vw_RvtGrids g 
    ON wh.health_check_id = g.health_check_id
WHERE wh.mapping_status = 'Mapped';

GO

PRINT 'Successfully created vw_RevitHealth_GridsWithProjects';
GO

-- =====================================================================
-- Revit Levels with Project Context
-- =====================================================================

IF OBJECT_ID('dbo.vw_RevitHealth_LevelsWithProjects', 'V') IS NOT NULL
    DROP VIEW dbo.vw_RevitHealth_LevelsWithProjects;
GO

CREATE VIEW dbo.vw_RevitHealth_LevelsWithProjects AS
SELECT
    wh.pm_project_id,
    wh.pm_project_name,
    wh.project_status,
    wh.client_name,
    wh.health_check_id,
    wh.revit_file_name,
    wh.export_date,
    l.*
FROM dbo.vw_RevitHealthWarehouse_CrossDB wh
INNER JOIN dbo.vw_RvtLevels l 
    ON wh.health_check_id = l.health_check_id
WHERE wh.mapping_status = 'Mapped';

GO

PRINT 'Successfully created vw_RevitHealth_LevelsWithProjects';
GO

-- =====================================================================
-- Revit Coordinates with Project Context
-- =====================================================================

IF OBJECT_ID('dbo.vw_RevitHealth_CoordinatesWithProjects', 'V') IS NOT NULL
    DROP VIEW dbo.vw_RevitHealth_CoordinatesWithProjects;
GO

CREATE VIEW dbo.vw_RevitHealth_CoordinatesWithProjects AS
SELECT
    wh.pm_project_id,
    wh.pm_project_name,
    wh.project_status,
    wh.client_name,
    wh.health_check_id,
    wh.revit_file_name,
    wh.export_date,
    c.*
FROM dbo.vw_RevitHealthWarehouse_CrossDB wh
INNER JOIN dbo.vw_RvtCoordinates c 
    ON wh.health_check_id = c.health_check_id
WHERE wh.mapping_status = 'Mapped';

GO

PRINT 'Successfully created vw_RevitHealth_CoordinatesWithProjects';
GO
