-- ServiceTemplates table for reusable service definitions
CREATE TABLE [dbo].[ServiceTemplates] (
    [ID] INT IDENTITY(1,1) PRIMARY KEY,
    [TemplateName] NVARCHAR(128) NOT NULL,
    [Description] NVARCHAR(512),
    [ServiceType] NVARCHAR(64) NOT NULL,
    [Parameters] NVARCHAR(MAX), -- JSON or delimited string for service parameters
    [CreatedBy] NVARCHAR(64),
    [CreatedAt] DATETIME2 DEFAULT GETDATE(),
    [IsActive] BIT DEFAULT 1
);

-- Index for quick lookup by name/type
CREATE INDEX IX_ServiceTemplates_TemplateName ON [dbo].[ServiceTemplates] ([TemplateName]);
CREATE INDEX IX_ServiceTemplates_ServiceType ON [dbo].[ServiceTemplates] ([ServiceType]);
