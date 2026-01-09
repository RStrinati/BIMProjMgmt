USE ProjectManagement;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'ix_stg_issues_source_issue' AND object_id = OBJECT_ID('stg.issues')
)
CREATE NONCLUSTERED INDEX ix_stg_issues_source_issue
    ON stg.issues (source_system, issue_id, source_load_ts)
    INCLUDE (project_id_raw, status, priority_normalized, created_at, closed_at);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'ix_stg_issue_attributes_issue' AND object_id = OBJECT_ID('stg.issue_attributes')
)
CREATE NONCLUSTERED INDEX ix_stg_issue_attributes_issue
    ON stg.issue_attributes (source_system, issue_id, attribute_name, source_load_ts)
    INCLUDE (mapped_field_name, attribute_value);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'ix_dim_issue_project' AND object_id = OBJECT_ID('dim.issue')
)
CREATE NONCLUSTERED INDEX ix_dim_issue_project
    ON dim.issue (project_sk, current_flag)
    INCLUDE (status, status_normalized, priority_normalized, is_deleted);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'ix_fact_issue_snapshot_date' AND object_id = OBJECT_ID('fact.issue_snapshot')
)
CREATE NONCLUSTERED INDEX ix_fact_issue_snapshot_date
    ON fact.issue_snapshot (snapshot_date_sk, project_sk, issue_sk)
    INCLUDE (is_open, is_closed, backlog_age_days, resolution_days);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'ix_fact_issue_snapshot_trends' AND object_id = OBJECT_ID('fact.issue_snapshot')
)
CREATE NONCLUSTERED INDEX ix_fact_issue_snapshot_trends
    ON fact.issue_snapshot (snapshot_date_sk, project_sk, client_sk, project_type_sk)
    INCLUDE (is_open, is_closed, backlog_age_days, resolution_days, urgency_score, sentiment_score);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'ix_dim_project_bk' AND object_id = OBJECT_ID('dim.project')
)
CREATE NONCLUSTERED INDEX ix_dim_project_bk
    ON dim.project (project_bk)
    INCLUDE (project_sk, current_flag);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'ix_dim_client_bk' AND object_id = OBJECT_ID('dim.client')
)
CREATE NONCLUSTERED INDEX ix_dim_client_bk
    ON dim.client (client_bk)
    INCLUDE (client_sk);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'ix_dim_project_type_bk' AND object_id = OBJECT_ID('dim.project_type')
)
CREATE NONCLUSTERED INDEX ix_dim_project_type_bk
    ON dim.project_type (project_type_bk)
    INCLUDE (project_type_sk);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'ix_ctl_data_quality_run' AND object_id = OBJECT_ID('ctl.data_quality_result')
)
CREATE NONCLUSTERED INDEX ix_ctl_data_quality_run
    ON ctl.data_quality_result (run_id, severity, passed);
GO
