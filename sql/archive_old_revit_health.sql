/*
    Revit Health Check archival script
    ----------------------------------
    Moves historic records out of RevitHealthCheckDB.dbo.tblRvtProjHealth
    into a separate archive database so the primary DB stays under the SQL
    Server Express 10 GB limit.

    Usage:
      1. Adjust @CutoffDate / @BatchSize to suit.
      2. Execute from SQL Server Management Studio (SSMS) or sqlcmd.
      3. After the script completes, shrink RevitHealthCheckDB if desired.

    The script will:
      - Create RevitHealthCheckArchiveDB if it does not exist.
      - Create an archive table with the same schema (first run only).
      - Move data in batches using DELETE ... OUTPUT for safety.
*/

USE master;
GO

IF DB_ID(N'RevitHealthCheckArchiveDB') IS NULL
BEGIN
    PRINT N'Creating RevitHealthCheckArchiveDB...';
    EXEC(N'CREATE DATABASE [RevitHealthCheckArchiveDB]');
END
GO

IF OBJECT_ID(N'RevitHealthCheckArchiveDB.dbo.tblRvtProjHealth', N'U') IS NULL
BEGIN
    PRINT N'Creating archive table RevitHealthCheckArchiveDB.dbo.tblRvtProjHealth...';
    EXEC(N'
        SELECT TOP (0) *
        INTO RevitHealthCheckArchiveDB.dbo.tblRvtProjHealth
        FROM RevitHealthCheckDB.dbo.tblRvtProjHealth
    ');

    -- Optional: preserve clustered index on nId for faster lookups in archive
    EXEC(N'
        CREATE CLUSTERED INDEX IX_tblRvtProjHealthArchive_nId
        ON RevitHealthCheckArchiveDB.dbo.tblRvtProjHealth (nId)
    ');
END
GO

DECLARE @CutoffDate DATE       = DATEADD(YEAR, -1, GETDATE()); -- adjust as needed
DECLARE @BatchSize   INT       = 5000;                         -- tune for your environment
DECLARE @RowsMoved   INT       = 1;

PRINT CONCAT('Archiving rows with ConvertedExportedDate < ', CONVERT(varchar(10), @CutoffDate, 120));

WHILE @RowsMoved > 0
BEGIN
    ;WITH cte AS (
        SELECT TOP (@BatchSize) *
        FROM RevitHealthCheckDB.dbo.tblRvtProjHealth
        WHERE ConvertedExportedDate IS NOT NULL
          AND ConvertedExportedDate < @CutoffDate
        ORDER BY ConvertedExportedDate, nId
    )
    DELETE FROM cte
    OUTPUT deleted.*
    INTO RevitHealthCheckArchiveDB.dbo.tblRvtProjHealth;

    SET @RowsMoved = @@ROWCOUNT;

    IF @RowsMoved > 0
    BEGIN
        PRINT CONCAT('Moved batch of ', @RowsMoved, ' rows to archive...');
    END
END

PRINT 'Archival run complete. Review archive DB and shrink primary DB if desired.';
