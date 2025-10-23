-- Extend tasks table with fields required for the Tasks & Notes view feature.

IF OBJECT_ID('dbo.tasks', 'U') IS NULL
BEGIN
    RAISERROR('Cannot alter table "tasks" because it does not exist in the current database. Run this migration against the ProjectManagement database after creating the base table.', 16, 1);
    RETURN;
END;

IF EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID('dbo.tasks')
      AND name = 'cycle_id'
      AND is_nullable = 0
)
BEGIN
    ALTER TABLE dbo.tasks
        ALTER COLUMN cycle_id INT NULL;
END;

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID('dbo.tasks')
      AND name = 'task_date'
)
BEGIN
    ALTER TABLE dbo.tasks
        ADD task_date DATE NULL;
END;

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID('dbo.tasks')
      AND name = 'time_start'
)
BEGIN
    ALTER TABLE dbo.tasks
        ADD time_start TIME NULL;
END;

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID('dbo.tasks')
      AND name = 'time_end'
)
BEGIN
    ALTER TABLE dbo.tasks
        ADD time_end TIME NULL;
END;

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID('dbo.tasks')
      AND name = 'time_spent_minutes'
)
BEGIN
    ALTER TABLE dbo.tasks
        ADD time_spent_minutes INT NULL;
END;

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID('dbo.tasks')
      AND name = 'task_items'
)
BEGIN
    ALTER TABLE dbo.tasks
        ADD task_items NVARCHAR(MAX) NULL;
END;

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID('dbo.tasks')
      AND name = 'notes'
)
BEGIN
    ALTER TABLE dbo.tasks
        ADD notes NVARCHAR(MAX) NULL;
END;

DECLARE @statusColumnId INT = NULL;
DECLARE @existingDefaultName SYSNAME = NULL;
DECLARE @existingDefaultDefinition NVARCHAR(MAX) = NULL;

SELECT
    @statusColumnId = c.column_id,
    @existingDefaultName = dc.name,
    @existingDefaultDefinition = dc.definition
FROM sys.columns c
LEFT JOIN sys.default_constraints dc
    ON dc.parent_object_id = c.object_id
    AND dc.parent_column_id = c.column_id
WHERE c.object_id = OBJECT_ID('dbo.tasks')
  AND c.name = 'status';

IF @statusColumnId IS NOT NULL
BEGIN
    IF @existingDefaultName IS NOT NULL
    BEGIN
        DECLARE @normalizedDefinition NVARCHAR(MAX) = LOWER(REPLACE(REPLACE(REPLACE(@existingDefaultDefinition, '(', ''), ')', ''), ' ', ''));
        IF @normalizedDefinition NOT IN ('''active''', 'active')
        BEGIN
            EXEC('ALTER TABLE dbo.tasks DROP CONSTRAINT [' + @existingDefaultName + ']');
            SET @existingDefaultName = NULL;
        END;
    END;

    IF @existingDefaultName IS NULL
    BEGIN
        ALTER TABLE dbo.tasks
            ADD CONSTRAINT DF_Tasks_Status DEFAULT ('active') FOR status;
    END;
END;
