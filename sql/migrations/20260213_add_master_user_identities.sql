-- 20260213: Master user identity normalization
USE ProjectManagement;

IF OBJECT_ID('dbo.master_users', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.master_users (
        master_user_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        email_normalized NVARCHAR(255) NOT NULL,
        display_name NVARCHAR(255) NULL,
        company NVARCHAR(255) NULL,
        status NVARCHAR(64) NULL,
        last_active_at DATETIME2 NULL,
        created_at DATETIME2 NOT NULL CONSTRAINT DF_master_users_created_at DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL CONSTRAINT DF_master_users_updated_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT UQ_master_users_email UNIQUE (email_normalized)
    );

    CREATE INDEX IX_master_users_last_active ON dbo.master_users(last_active_at);
END;

IF OBJECT_ID('dbo.master_user_identities', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.master_user_identities (
        master_user_id INT NOT NULL,
        source_system NVARCHAR(32) NOT NULL,
        source_user_id NVARCHAR(100) NOT NULL,
        email_normalized NVARCHAR(255) NULL,
        name NVARCHAR(255) NULL,
        company NVARCHAR(255) NULL,
        role NVARCHAR(255) NULL,
        status NVARCHAR(64) NULL,
        last_active_at DATETIME2 NULL,
        user_key NVARCHAR(160) NULL,
        synced_at DATETIME2 NOT NULL CONSTRAINT DF_master_user_identities_synced_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_master_user_identities PRIMARY KEY (source_system, source_user_id),
        CONSTRAINT FK_master_user_identities_master_users FOREIGN KEY (master_user_id)
            REFERENCES dbo.master_users(master_user_id)
    );

    CREATE INDEX IX_master_user_identities_email ON dbo.master_user_identities(email_normalized);
    CREATE INDEX IX_master_user_identities_master_user_id ON dbo.master_user_identities(master_user_id);
END;
