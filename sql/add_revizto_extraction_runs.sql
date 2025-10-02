-- Create ReviztoExtractionRuns table to track Revizto data extraction runs
CREATE TABLE [dbo].[ReviztoExtractionRuns] (
    [run_id] INT IDENTITY(1,1) PRIMARY KEY,
    [start_time] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    [end_time] DATETIME2 NULL,
    [status] NVARCHAR(50) NOT NULL DEFAULT 'running', -- 'running', 'completed', 'failed'
    [projects_extracted] INT DEFAULT 0,
    [issues_extracted] INT DEFAULT 0,
    [licenses_extracted] INT DEFAULT 0,
    [export_folder] NVARCHAR(500) NULL,
    [notes] NVARCHAR(MAX) NULL
);

-- Create index on start_time for efficient querying
CREATE INDEX IX_ReviztoExtractionRuns_StartTime ON [dbo].[ReviztoExtractionRuns] ([start_time] DESC);

-- Create index on status for filtering
CREATE INDEX IX_ReviztoExtractionRuns_Status ON [dbo].[ReviztoExtractionRuns] ([status]);