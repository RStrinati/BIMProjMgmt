IF NOT EXISTS (
    SELECT * FROM sys.columns
    WHERE Name = 'assigned_to'
      AND Object_ID = OBJECT_ID('ReviewSchedule')
)
    ALTER TABLE ReviewSchedule ADD assigned_to INT NULL;
GO
IF NOT EXISTS (
    SELECT * FROM sys.columns
    WHERE Name = 'status'
      AND Object_ID = OBJECT_ID('ReviewSchedule')
)
    ALTER TABLE ReviewSchedule ADD status NVARCHAR(50);
GO
