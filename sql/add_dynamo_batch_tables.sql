-- =====================================================
-- Dynamo Batch Automation Tables
-- =====================================================
-- Creates tables for managing batch Dynamo script execution
-- via RevitBatchProcessor integration

-- Table: DynamoScripts
-- Stores registered Dynamo scripts available for batch execution
CREATE TABLE [dbo].[DynamoScripts] (
    [script_id] INT IDENTITY(1,1) PRIMARY KEY,
    [script_name] NVARCHAR(255) NOT NULL,
    [script_path] NVARCHAR(500) NOT NULL,
    [description] NVARCHAR(MAX) NULL,
    [category] NVARCHAR(100) NULL, -- 'Health Check', 'QA/QC', 'Export', 'Analysis'
    [output_folder] NVARCHAR(500) NULL, -- Default output location for JSON/CSV exports
    [is_active] BIT NOT NULL DEFAULT 1,
    [created_date] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    [modified_date] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    CONSTRAINT UQ_DynamoScripts_ScriptPath UNIQUE ([script_path])
);

-- Table: DynamoBatchJobs
-- Tracks batch execution jobs with RevitBatchProcessor
CREATE TABLE [dbo].[DynamoBatchJobs] (
    [job_id] INT IDENTITY(1,1) PRIMARY KEY,
    [job_name] NVARCHAR(255) NOT NULL,
    [script_id] INT NOT NULL,
    [project_id] INT NULL, -- Optional: link to specific project
    [created_by] INT NULL, -- Optional: link to user
    [status] NVARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'queued', 'running', 'completed', 'failed', 'cancelled'
    [created_date] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    [start_time] DATETIME2 NULL,
    [end_time] DATETIME2 NULL,
    [total_files] INT DEFAULT 0,
    [processed_files] INT DEFAULT 0,
    [success_count] INT DEFAULT 0,
    [error_count] INT DEFAULT 0,
    [task_file_path] NVARCHAR(500) NULL, -- Path to RevitBatchProcessor task JSON file
    [output_folder] NVARCHAR(500) NULL,
    [log_file_path] NVARCHAR(500) NULL,
    [error_message] NVARCHAR(MAX) NULL,
    [configuration] NVARCHAR(MAX) NULL, -- JSON configuration: {detach, audit, timeout, etc.}
    CONSTRAINT FK_DynamoBatchJobs_DynamoScripts FOREIGN KEY ([script_id]) REFERENCES [dbo].[DynamoScripts]([script_id]),
    CONSTRAINT FK_DynamoBatchJobs_Projects FOREIGN KEY ([project_id]) REFERENCES [dbo].[Projects]([project_id])
);

-- Table: DynamoBatchJobFiles
-- Individual file-level tracking within a batch job
CREATE TABLE [dbo].[DynamoBatchJobFiles] (
    [job_file_id] INT IDENTITY(1,1) PRIMARY KEY,
    [job_id] INT NOT NULL,
    [file_path] NVARCHAR(500) NOT NULL,
    [file_name] NVARCHAR(255) NOT NULL,
    [status] NVARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed', 'skipped'
    [start_time] DATETIME2 NULL,
    [end_time] DATETIME2 NULL,
    [error_message] NVARCHAR(MAX) NULL,
    [output_file_path] NVARCHAR(500) NULL, -- Path to generated JSON/CSV output
    [revit_version] NVARCHAR(50) NULL,
    CONSTRAINT FK_DynamoBatchJobFiles_Jobs FOREIGN KEY ([job_id]) REFERENCES [dbo].[DynamoBatchJobs]([job_id]) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IX_DynamoScripts_Category ON [dbo].[DynamoScripts]([category]);
CREATE INDEX IX_DynamoScripts_IsActive ON [dbo].[DynamoScripts]([is_active]);

CREATE INDEX IX_DynamoBatchJobs_Status ON [dbo].[DynamoBatchJobs]([status]);
CREATE INDEX IX_DynamoBatchJobs_CreatedDate ON [dbo].[DynamoBatchJobs]([created_date] DESC);
CREATE INDEX IX_DynamoBatchJobs_ProjectId ON [dbo].[DynamoBatchJobs]([project_id]);
CREATE INDEX IX_DynamoBatchJobs_ScriptId ON [dbo].[DynamoBatchJobs]([script_id]);

CREATE INDEX IX_DynamoBatchJobFiles_JobId ON [dbo].[DynamoBatchJobFiles]([job_id]);
CREATE INDEX IX_DynamoBatchJobFiles_Status ON [dbo].[DynamoBatchJobFiles]([status]);

-- Insert sample health check scripts (update paths as needed)
INSERT INTO [dbo].[DynamoScripts] ([script_name], [script_path], [description], [category], [output_folder])
VALUES 
    ('Model Health Check', 'C:\DynamoScripts\HealthCheck.dyn', 'Comprehensive Revit model health analysis with JSON export', 'Health Check', 'C:\Exports\DynamoHealth'),
    ('Family Size Analysis', 'C:\DynamoScripts\FamilySizeAnalysis.dyn', 'Analyzes family sizes and complexity metrics', 'Health Check', 'C:\Exports\DynamoHealth'),
    ('Naming Convention Check', 'C:\DynamoScripts\NamingCheck.dyn', 'Validates element naming against project standards', 'QA/QC', 'C:\Exports\DynamoHealth');

PRINT 'Dynamo batch automation tables created successfully';
