-- 20260213: ProjectManagement Revizto users + licenses copy
USE ProjectManagement;

IF OBJECT_ID('dbo.revizto_licenses', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.revizto_licenses (
        license_uuid NVARCHAR(100) NOT NULL PRIMARY KEY,
        name NVARCHAR(255) NULL,
        region NVARCHAR(64) NULL,
        expires DATETIME2 NULL,
        created DATETIME2 NULL,
        owner_id INT NULL,
        owner_uuid NVARCHAR(100) NULL,
        owner_email NVARCHAR(255) NULL,
        plan_users INT NULL,
        plan_projects INT NULL,
        slots_projects INT NULL,
        slots_users INT NULL,
        clash_automation BIT NULL,
        allow_be_external_guest BIT NULL,
        allow_guests_here BIT NULL,
        allow_bcf_export BIT NULL,
        allow_api_access BIT NULL,
        synced_at DATETIME2 NOT NULL CONSTRAINT DF_revizto_licenses_synced_at DEFAULT SYSUTCDATETIME()
    );
END;

IF OBJECT_ID('dbo.revizto_license_members', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.revizto_license_members (
        license_uuid NVARCHAR(100) NOT NULL,
        member_uuid NVARCHAR(100) NOT NULL,
        email NVARCHAR(255) NULL,
        invited_at DATETIME2 NULL,
        activated BIT NULL,
        deactivated BIT NULL,
        last_active DATETIME2 NULL,
        member_json NVARCHAR(MAX) NULL,
        synced_at DATETIME2 NOT NULL CONSTRAINT DF_revizto_license_members_synced_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_revizto_license_members PRIMARY KEY (license_uuid, member_uuid)
    );

    CREATE INDEX IX_revizto_license_members_email ON dbo.revizto_license_members(email);
    CREATE INDEX IX_revizto_license_members_last_active ON dbo.revizto_license_members(last_active);
END;
