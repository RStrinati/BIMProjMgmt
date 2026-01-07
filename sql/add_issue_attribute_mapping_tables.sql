USE ProjectManagement;
GO

IF OBJECT_ID('dbo.issue_attribute_map', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.issue_attribute_map (
        map_id              INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        project_id          NVARCHAR(255) NULL,
        source_system       NVARCHAR(32)  NOT NULL,
        raw_attribute_name  NVARCHAR(255) NOT NULL,
        mapped_field_name   NVARCHAR(100) NOT NULL,
        data_type           NVARCHAR(50)  NULL,
        priority            INT           NOT NULL CONSTRAINT DF_issue_attribute_map_priority DEFAULT 100,
        is_active           BIT           NOT NULL CONSTRAINT DF_issue_attribute_map_active DEFAULT 1,
        created_at          DATETIME2     NOT NULL CONSTRAINT DF_issue_attribute_map_created_at DEFAULT SYSUTCDATETIME(),
        updated_at          DATETIME2     NULL
    );
END
GO

IF OBJECT_ID('stg.issue_attributes', 'U') IS NULL
BEGIN
    CREATE TABLE stg.issue_attributes (
        source_system       NVARCHAR(32)  NOT NULL,
        issue_id            NVARCHAR(255) NOT NULL,
        project_id_raw      NVARCHAR(255) NULL,
        attribute_name      NVARCHAR(255) NOT NULL,
        attribute_value     NVARCHAR(MAX) NULL,
        attribute_type      NVARCHAR(50)  NULL,
        attribute_created_at DATETIME2    NULL,
        mapped_field_name   NVARCHAR(100) NULL,
        map_priority        INT           NULL,
        record_source       NVARCHAR(50)  NOT NULL,
        source_load_ts      DATETIME2     NOT NULL CONSTRAINT DF_stg_issue_attributes_source_load_ts DEFAULT SYSUTCDATETIME(),
        record_hash         BINARY(32)    NULL,
        CONSTRAINT pk_stg_issue_attributes PRIMARY KEY (source_system, issue_id, attribute_name, source_load_ts)
    );
END
GO
