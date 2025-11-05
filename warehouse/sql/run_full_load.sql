/*
    Warehouse full load orchestrator
    - Assumes staging tables stg.* have been populated recently
    - Loads dimensions (SCD2), then facts, then bridges
*/

USE ProjectManagement;
GO

PRINT '--- Load DATE dimension';
EXEC warehouse.usp_load_dim_date @StartDate='2019-01-01', @EndDate='2035-12-31';

PRINT '--- Load LOOKUP dimensions';
EXEC warehouse.usp_load_dim_client;
EXEC warehouse.usp_load_dim_project_type;
EXEC warehouse.usp_load_dim_project;
EXEC warehouse.usp_load_dim_user;
EXEC warehouse.usp_load_dim_issue_category;
EXEC warehouse.usp_load_dim_service;
EXEC warehouse.usp_load_dim_review_stage;  -- currently placeholder
EXEC warehouse.usp_load_dim_review_cycle;

PRINT '--- Load FACTS';
EXEC warehouse.usp_load_fact_issue_snapshot;
EXEC warehouse.usp_load_fact_issue_activity;
EXEC warehouse.usp_load_fact_service_monthly;
EXEC warehouse.usp_load_fact_review_cycle;
EXEC warehouse.usp_load_fact_review_event; -- placeholder
EXEC warehouse.usp_load_fact_project_kpi_monthly;

PRINT '--- Load BRIDGES';
EXEC warehouse.usp_load_bridges;

PRINT 'Warehouse full load complete.';
GO
