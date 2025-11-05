USE ProjectManagement;
GO

IF OBJECT_ID('dbo.vw_dim_projects', 'V') IS NOT NULL
    DROP VIEW dbo.vw_dim_projects;
GO

CREATE VIEW dbo.vw_dim_projects AS
SELECT
    p.project_bk   AS pm_project_id,
    p.project_name AS project_name,
    p.status,
    p.priority,
    p.client_sk,
    p.project_type_sk
FROM dim.project p
WHERE p.current_flag = 1;
GO
