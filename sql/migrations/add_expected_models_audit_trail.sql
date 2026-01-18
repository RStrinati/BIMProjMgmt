-- Phase 2: Version History + Audit Trail for Quality Register
-- Track all changes to ExpectedModels for full audit trail

USE ProjectManagement;
GO

-- Create audit history table for ExpectedModels
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'ExpectedModelsHistory')
BEGIN
    CREATE TABLE ExpectedModelsHistory (
        history_id INT IDENTITY(1,1) PRIMARY KEY,
        expected_model_id INT NOT NULL,
        project_id INT NOT NULL,
        
        -- Snapshot of all fields at time of change
        abv NVARCHAR(10) NULL,
        registered_model_name NVARCHAR(255) NULL,
        company NVARCHAR(255) NULL,
        discipline NVARCHAR(100) NULL,
        description NVARCHAR(MAX) NULL,
        bim_contact NVARCHAR(255) NULL,
        notes NVARCHAR(MAX) NULL,
        
        -- Audit metadata
        change_type NVARCHAR(20) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
        changed_fields NVARCHAR(MAX) NULL, -- JSON array of changed field names
        changed_by NVARCHAR(255) NULL, -- User who made the change (future)
        changed_at DATETIME NOT NULL DEFAULT GETDATE(),
        
        -- Reference to original record
        FOREIGN KEY (expected_model_id) REFERENCES ExpectedModels(expected_model_id),
        FOREIGN KEY (project_id) REFERENCES projects(project_id)
    );
    
    CREATE INDEX IDX_ExpectedModelsHistory_ModelId ON ExpectedModelsHistory(expected_model_id);
    CREATE INDEX IDX_ExpectedModelsHistory_ProjectId ON ExpectedModelsHistory(project_id);
    CREATE INDEX IDX_ExpectedModelsHistory_ChangedAt ON ExpectedModelsHistory(changed_at DESC);
    
    PRINT '✅ Created ExpectedModelsHistory table';
END
ELSE
    PRINT 'ExpectedModelsHistory table already exists';
GO

-- Create trigger to automatically track changes
IF OBJECT_ID('trg_ExpectedModels_AuditTrail', 'TR') IS NOT NULL
    DROP TRIGGER trg_ExpectedModels_AuditTrail;
GO

CREATE TRIGGER trg_ExpectedModels_AuditTrail
ON ExpectedModels
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @ChangeType NVARCHAR(20);
    DECLARE @ChangedFields NVARCHAR(MAX);
    
    -- Handle INSERT
    IF EXISTS (SELECT * FROM inserted) AND NOT EXISTS (SELECT * FROM deleted)
    BEGIN
        SET @ChangeType = 'INSERT';
        SET @ChangedFields = '[]'; -- No changed fields for insert
        
        INSERT INTO ExpectedModelsHistory (
            expected_model_id, project_id, abv, registered_model_name,
            company, discipline, description, bim_contact, notes,
            change_type, changed_fields, changed_at
        )
        SELECT 
            expected_model_id, project_id, abv, registered_model_name,
            company, discipline, description, bim_contact, notes,
            @ChangeType, @ChangedFields, GETDATE()
        FROM inserted;
    END
    
    -- Handle UPDATE
    IF EXISTS (SELECT * FROM inserted) AND EXISTS (SELECT * FROM deleted)
    BEGIN
        SET @ChangeType = 'UPDATE';
        
        INSERT INTO ExpectedModelsHistory (
            expected_model_id, project_id, abv, registered_model_name,
            company, discipline, description, bim_contact, notes,
            change_type, changed_fields, changed_at
        )
        SELECT 
            i.expected_model_id, i.project_id, i.abv, i.registered_model_name,
            i.company, i.discipline, i.description, i.bim_contact, i.notes,
            @ChangeType,
            -- Build JSON array of changed fields
            '[' + 
            CASE WHEN ISNULL(i.abv, '') != ISNULL(d.abv, '') THEN '"abv",' ELSE '' END +
            CASE WHEN ISNULL(i.registered_model_name, '') != ISNULL(d.registered_model_name, '') THEN '"registered_model_name",' ELSE '' END +
            CASE WHEN ISNULL(i.company, '') != ISNULL(d.company, '') THEN '"company",' ELSE '' END +
            CASE WHEN ISNULL(i.discipline, '') != ISNULL(d.discipline, '') THEN '"discipline",' ELSE '' END +
            CASE WHEN ISNULL(i.description, '') != ISNULL(d.description, '') THEN '"description",' ELSE '' END +
            CASE WHEN ISNULL(i.bim_contact, '') != ISNULL(d.bim_contact, '') THEN '"bim_contact",' ELSE '' END +
            CASE WHEN ISNULL(i.notes, '') != ISNULL(d.notes, '') THEN '"notes",' ELSE '' END +
            ']',
            GETDATE()
        FROM inserted i
        INNER JOIN deleted d ON i.expected_model_id = d.expected_model_id;
    END
    
    -- Handle DELETE
    IF NOT EXISTS (SELECT * FROM inserted) AND EXISTS (SELECT * FROM deleted)
    BEGIN
        SET @ChangeType = 'DELETE';
        SET @ChangedFields = '[]';
        
        INSERT INTO ExpectedModelsHistory (
            expected_model_id, project_id, abv, registered_model_name,
            company, discipline, description, bim_contact, notes,
            change_type, changed_fields, changed_at
        )
        SELECT 
            expected_model_id, project_id, abv, registered_model_name,
            company, discipline, description, bim_contact, notes,
            @ChangeType, @ChangedFields, GETDATE()
        FROM deleted;
    END
END;
GO

PRINT '';
PRINT '✅ Phase 2 audit trail complete - all changes to ExpectedModels will be tracked';
GO
