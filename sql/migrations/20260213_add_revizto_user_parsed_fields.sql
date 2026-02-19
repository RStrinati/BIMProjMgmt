-- 20260213: Add parsed Revizto member fields
USE ProjectManagement;

IF COL_LENGTH('dbo.revizto_license_members', 'full_name') IS NULL
BEGIN
    ALTER TABLE dbo.revizto_license_members ADD full_name NVARCHAR(255) NULL;
END;

IF COL_LENGTH('dbo.revizto_license_members', 'role_name') IS NULL
BEGIN
    ALTER TABLE dbo.revizto_license_members ADD role_name NVARCHAR(255) NULL;
END;

IF COL_LENGTH('dbo.revizto_license_members', 'company_name') IS NULL
BEGIN
    ALTER TABLE dbo.revizto_license_members ADD company_name NVARCHAR(255) NULL;
END;

IF COL_LENGTH('dbo.revizto_license_members', 'last_active_source') IS NULL
BEGIN
    ALTER TABLE dbo.revizto_license_members ADD last_active_source NVARCHAR(32) NULL;
END;

IF COL_LENGTH('dbo.revizto_license_members', 'revizto_project_count') IS NULL
BEGIN
    ALTER TABLE dbo.revizto_license_members ADD revizto_project_count INT NULL;
END;
