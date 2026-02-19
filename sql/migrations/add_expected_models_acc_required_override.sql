-- Add ACC required override flag for quality register
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'ExpectedModels'
      AND COLUMN_NAME = 'acc_required_override'
)
BEGIN
    ALTER TABLE ExpectedModels
    ADD acc_required_override BIT NULL;
END;
