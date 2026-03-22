-- =====================================================
-- IFC IDS Validation Tables
-- =====================================================

CREATE TABLE [dbo].[IfcIdsTests] (
    [ids_test_id] INT IDENTITY(1,1) PRIMARY KEY,
    [project_id] INT NOT NULL,
    [ids_name] NVARCHAR(255) NOT NULL,
    [ids_content] NVARCHAR(MAX) NOT NULL,
    [is_active] BIT NOT NULL DEFAULT 1,
    [created_at] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    [updated_at] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    CONSTRAINT FK_IfcIdsTests_Projects FOREIGN KEY ([project_id]) REFERENCES [dbo].[Projects]([project_id])
);

CREATE TABLE [dbo].[IfcValidationRuns] (
    [validation_run_id] INT IDENTITY(1,1) PRIMARY KEY,
    [project_id] INT NOT NULL,
    [expected_model_id] INT NULL,
    [ids_test_id] INT NULL,
    [ifc_filename] NVARCHAR(255) NOT NULL,
    [ids_filename] NVARCHAR(255) NOT NULL,
    [status] NVARCHAR(50) NOT NULL DEFAULT 'queued', -- queued, running, completed, failed
    [started_at] DATETIME2 NULL,
    [completed_at] DATETIME2 NULL,
    [total_specifications] INT NULL,
    [passed_specifications] INT NULL,
    [failed_specifications] INT NULL,
    [total_failures] INT NULL,
    [html_report] NVARCHAR(MAX) NULL,
    [error_message] NVARCHAR(MAX) NULL,
    [created_at] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    [updated_at] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    CONSTRAINT FK_IfcValidationRuns_Projects FOREIGN KEY ([project_id]) REFERENCES [dbo].[Projects]([project_id]),
    CONSTRAINT FK_IfcValidationRuns_ExpectedModels FOREIGN KEY ([expected_model_id]) REFERENCES [dbo].[ExpectedModels]([expected_model_id]),
    CONSTRAINT FK_IfcValidationRuns_IfcIdsTests FOREIGN KEY ([ids_test_id]) REFERENCES [dbo].[IfcIdsTests]([ids_test_id])
);

CREATE TABLE [dbo].[IfcValidationFailures] (
    [failure_id] INT IDENTITY(1,1) PRIMARY KEY,
    [validation_run_id] INT NOT NULL,
    [specification_name] NVARCHAR(255) NOT NULL,
    [message] NVARCHAR(MAX) NULL,
    [ifc_class] NVARCHAR(128) NULL,
    [object_name] NVARCHAR(255) NULL,
    [created_at] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    CONSTRAINT FK_IfcValidationFailures_Runs FOREIGN KEY ([validation_run_id]) REFERENCES [dbo].[IfcValidationRuns]([validation_run_id]) ON DELETE CASCADE
);

CREATE INDEX IX_IfcIdsTests_ProjectId ON [dbo].[IfcIdsTests]([project_id]);
CREATE INDEX IX_IfcValidationRuns_ProjectId ON [dbo].[IfcValidationRuns]([project_id]);
CREATE INDEX IX_IfcValidationRuns_Status ON [dbo].[IfcValidationRuns]([status]);
CREATE INDEX IX_IfcValidationFailures_RunId ON [dbo].[IfcValidationFailures]([validation_run_id]);

PRINT 'IFC IDS validation tables created successfully';
