/*
    Bridge / Helper Tables for Many-to-Many Relationships
*/

USE [ProjectManagement];
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'brg')
BEGIN
    EXEC('CREATE SCHEMA brg AUTHORIZATION dbo;');
END
GO

/* ISSUE CATEGORY BRIDGE */
IF OBJECT_ID('brg.issue_category', 'U') IS NULL
BEGIN
    CREATE TABLE brg.issue_category (
        issue_sk          INT          NOT NULL,
        issue_category_sk INT          NOT NULL,
        category_role     NVARCHAR(32) NOT NULL, -- discipline / primary / secondary / tag
        load_ts           DATETIME2    NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT pk_brg_issue_category PRIMARY KEY (issue_sk, issue_category_sk, category_role)
    );
END
GO

/* SERVICE STAGE BRIDGE */
IF OBJECT_ID('brg.service_stage', 'U') IS NULL
BEGIN
    CREATE TABLE brg.service_stage (
        service_sk INT NOT NULL,
        stage_sk   INT NOT NULL,
        load_ts    DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT pk_brg_service_stage PRIMARY KEY (service_sk, stage_sk)
    );
END
GO
