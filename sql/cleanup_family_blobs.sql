/*
    One-time clean up script to clear legacy family JSON blobs
    from tblRvtProjHealth after moving data to external storage.
    Run after verifying the new family summary pipeline.
*/

USE [RevitHealthCheckDB];
GO

UPDATE dbo.tblRvtProjHealth
SET
    jsonFamilies = NULL,
    jsonFamily_sizes = NULL
WHERE jsonFamilies IS NOT NULL
   OR jsonFamily_sizes IS NOT NULL;
GO
