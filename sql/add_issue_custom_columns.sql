USE ProjectManagement;
GO

IF COL_LENGTH('stg.issues', 'phase') IS NULL
    ALTER TABLE stg.issues ADD phase NVARCHAR(255) NULL;
GO

IF COL_LENGTH('stg.issues', 'building_level') IS NULL
    ALTER TABLE stg.issues ADD building_level NVARCHAR(255) NULL;
GO

IF COL_LENGTH('stg.issues', 'clash_level') IS NULL
    ALTER TABLE stg.issues ADD clash_level NVARCHAR(255) NULL;
GO

IF COL_LENGTH('stg.issues', 'custom_attributes_json') IS NULL
    ALTER TABLE stg.issues ADD custom_attributes_json NVARCHAR(MAX) NULL;
GO

IF COL_LENGTH('dim.issue', 'phase') IS NULL
    ALTER TABLE dim.issue ADD phase NVARCHAR(255) NULL;
GO

IF COL_LENGTH('dim.issue', 'building_level') IS NULL
    ALTER TABLE dim.issue ADD building_level NVARCHAR(255) NULL;
GO

IF COL_LENGTH('dim.issue', 'clash_level') IS NULL
    ALTER TABLE dim.issue ADD clash_level NVARCHAR(255) NULL;
GO

IF COL_LENGTH('dim.issue', 'custom_attributes_json') IS NULL
    ALTER TABLE dim.issue ADD custom_attributes_json NVARCHAR(MAX) NULL;
GO
