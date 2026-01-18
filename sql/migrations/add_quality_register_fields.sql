-- Phase 1D Quality Register - Add manual register fields to ExpectedModels
-- These fields are user-editable and form the core of the quality register

USE ProjectManagement;
GO

-- Check and add abv column
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ExpectedModels' AND COLUMN_NAME = 'abv')
BEGIN
    ALTER TABLE ExpectedModels ADD abv NVARCHAR(10) NULL;
    PRINT 'Added abv column';
END
ELSE
    PRINT 'abv column already exists';

-- Check and add registered_model_name column (canonical name for matching)
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ExpectedModels' AND COLUMN_NAME = 'registered_model_name')
BEGIN
    ALTER TABLE ExpectedModels ADD registered_model_name NVARCHAR(255) NULL;
    PRINT 'Added registered_model_name column';
END
ELSE
    PRINT 'registered_model_name column already exists';

-- Check and add company column  
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ExpectedModels' AND COLUMN_NAME = 'company')
BEGIN
    ALTER TABLE ExpectedModels ADD company NVARCHAR(255) NULL;
    PRINT 'Added company column';
END
ELSE
    PRINT 'company column already exists';

-- Check and add description column
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ExpectedModels' AND COLUMN_NAME = 'description')
BEGIN
    ALTER TABLE ExpectedModels ADD description NVARCHAR(MAX) NULL;
    PRINT 'Added description column';
END
ELSE
    PRINT 'description column already exists';

-- Check and add bim_contact column
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ExpectedModels' AND COLUMN_NAME = 'bim_contact')
BEGIN
    ALTER TABLE ExpectedModels ADD bim_contact NVARCHAR(255) NULL;
    PRINT 'Added bim_contact column';
END
ELSE
    PRINT 'bim_contact column already exists';

-- Check and add notes column (primary update mechanism)
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ExpectedModels' AND COLUMN_NAME = 'notes')
BEGIN
    ALTER TABLE ExpectedModels ADD notes NVARCHAR(MAX) NULL;
    PRINT 'Added notes column';
END
ELSE
    PRINT 'notes column already exists';

-- Check and add notes_updated_at column
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ExpectedModels' AND COLUMN_NAME = 'notes_updated_at')
BEGIN
    ALTER TABLE ExpectedModels ADD notes_updated_at DATETIME NULL;
    PRINT 'Added notes_updated_at column';
END
ELSE
    PRINT 'notes_updated_at column already exists';

PRINT '';
PRINT '✅ Phase 1D Quality Register field migration complete';
GO
