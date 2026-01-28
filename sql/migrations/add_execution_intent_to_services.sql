-- Add execution planning fields to ProjectServices
-- Enables marking services as optional or not proceeding without affecting contract value

IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'ProjectServices' AND COLUMN_NAME = 'execution_intent'
)
BEGIN
    ALTER TABLE ProjectServices
    ADD execution_intent VARCHAR(20) DEFAULT 'planned' NOT NULL
        CONSTRAINT CK_ProjectServices_execution_intent
        CHECK (execution_intent IN ('planned', 'optional', 'not_proceeding'));
    
    CREATE INDEX IX_ProjectServices_execution_intent
    ON ProjectServices(project_id, execution_intent);
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'ProjectServices' AND COLUMN_NAME = 'decision_reason'
)
BEGIN
    ALTER TABLE ProjectServices
    ADD decision_reason NVARCHAR(100) NULL;
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'ProjectServices' AND COLUMN_NAME = 'decision_at'
)
BEGIN
    ALTER TABLE ProjectServices
    ADD decision_at DATETIME NULL;
END;
GO

-- Add a computed column for easier querying
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'ProjectServices' AND COLUMN_NAME = 'is_planned_for_execution'
)
BEGIN
    ALTER TABLE ProjectServices
    ADD is_planned_for_execution AS (CASE WHEN execution_intent = 'planned' THEN 1 ELSE 0 END);
END;
GO

PRINT 'ProjectServices execution planning columns added successfully.';
