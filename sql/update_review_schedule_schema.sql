USE ProjectManagement;
GO

DECLARE @review_schedule_id INT = OBJECT_ID('dbo.ReviewSchedule');

IF @review_schedule_id IS NULL
BEGIN
    RAISERROR('ReviewSchedule table was not found in ProjectManagement database.', 16, 1);
    RETURN;
END;

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE Name = 'assigned_to'
      AND Object_ID = @review_schedule_id
)
    ALTER TABLE dbo.ReviewSchedule ADD assigned_to INT NULL;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE Name = 'status'
      AND Object_ID = @review_schedule_id
)
    ALTER TABLE dbo.ReviewSchedule ADD status NVARCHAR(50);
GO
