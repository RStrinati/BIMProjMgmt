-- =====================================================================
-- Wrapper views that align existing qry_* views with the warehouse
-- naming expected by downstream scripts. Run in RevitHealthCheckDB.
-- =====================================================================

USE RevitHealthCheckDB;
GO

IF OBJECT_ID('dbo.vw_RvtGrids', 'V') IS NOT NULL
    DROP VIEW dbo.vw_RvtGrids;
GO
CREATE VIEW dbo.vw_RvtGrids
AS
SELECT *
FROM dbo.qry_Grids;
GO

IF OBJECT_ID('dbo.vw_RvtLevels', 'V') IS NOT NULL
    DROP VIEW dbo.vw_RvtLevels;
GO
CREATE VIEW dbo.vw_RvtLevels
AS
SELECT *
FROM dbo.qry_Levels;
GO

IF OBJECT_ID('dbo.vw_RvtCoordinates', 'V') IS NOT NULL
    DROP VIEW dbo.vw_RvtCoordinates;
GO
CREATE VIEW dbo.vw_RvtCoordinates
AS
SELECT *
FROM dbo.qry_Coordinates;
GO

PRINT 'vw_Rvt* wrapper views refreshed.';
GO
