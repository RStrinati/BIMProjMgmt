-- Revizto Data Exporter - Database Setup Script
-- Run this script in SQL Server Management Studio or sqlcmd
-- Creates the ReviztoData database and necessary permissions

USE master;
GO

-- Create the database if it doesn't exist
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'ReviztoData')
BEGIN
    CREATE DATABASE ReviztoData;
    PRINT 'Database ReviztoData created successfully.';
END
ELSE
BEGIN
    PRINT 'Database ReviztoData already exists.';
END
GO

-- Use the ReviztoData database
USE ReviztoData;
GO

-- The application will create these tables automatically, but you can verify the structure here:
-- Tables that will be created by the application:
--
-- tblUserLicenses - Stores Revizto license information
-- tblLicenseMembers - Stores team members for each license  
-- tblReviztoProjects - Stores project metadata and details
-- tblReviztoProjectIssues - Stores all issues/tasks from projects
-- tblReviztoIssueComments - Stores comments and discussions

-- Optional: Create a dedicated user for the application (recommended for production)
-- Uncomment and modify the following section if you want to use SQL Server authentication:

/*
-- Create login and user for the application
CREATE LOGIN ReviztoExporter WITH PASSWORD = 'YourSecurePassword123!';
GO

USE ReviztoData;
GO

CREATE USER ReviztoExporter FOR LOGIN ReviztoExporter;
GO

-- Grant necessary permissions
ALTER ROLE db_datareader ADD MEMBER ReviztoExporter;
ALTER ROLE db_datawriter ADD MEMBER ReviztoExporter;
ALTER ROLE db_ddladmin ADD MEMBER ReviztoExporter;  -- Needed to create tables
GO

PRINT 'User ReviztoExporter created with appropriate permissions.';

-- If using SQL Server authentication, update your connection string to:
-- "Server=YOUR_SERVER;Database=ReviztoData;User Id=ReviztoExporter;Password=YourSecurePassword123!;"
*/

-- Verify database is ready
SELECT 
    'Database Setup Complete' as Status,
    DB_NAME() as DatabaseName,
    GETDATE() as SetupTime;

-- Show current database size (will be minimal initially)
SELECT 
    DB_NAME() as DatabaseName,
    CAST(SUM(CAST(FILEPROPERTY(name, 'SpaceUsed') AS bigint) * 8192.) / 1024 / 1024 AS DECIMAL(15,2)) AS 'Database Size (MB)',
    CAST(SUM(CAST(FILEPROPERTY(name, 'SpaceUsed') AS bigint) * 8192.) / 1024 / 1024 / 1024 AS DECIMAL(15,2)) AS 'Database Size (GB)'
FROM sys.database_files 
WHERE type_desc = 'ROWS';

PRINT 'ReviztoData database is ready for use.';
PRINT 'The application will create all necessary tables automatically on first run.';
PRINT 'Make sure to update your appsettings.json with the correct connection string.';
GO