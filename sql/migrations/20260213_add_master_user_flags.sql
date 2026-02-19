-- 20260213: Add master user flags for manual BIM meeting tracking
USE ProjectManagement;

IF OBJECT_ID('dbo.master_user_flags', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.master_user_flags (
        user_key NVARCHAR(120) NOT NULL PRIMARY KEY,
        invited_to_bim_meetings BIT NULL,
        is_watcher BIT NULL,
        is_assignee BIT NULL,
        updated_at DATETIME2 NOT NULL CONSTRAINT DF_master_user_flags_updated_at DEFAULT SYSUTCDATETIME()
    );
END;
