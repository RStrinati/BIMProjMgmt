USE acc_data_schema
GO

-- Create Hubs view using admin_accounts
IF EXISTS (SELECT * FROM sys.views WHERE name='vw_Hubs')
    DROP VIEW vw_Hubs
GO

CREATE VIEW vw_Hubs AS
SELECT DISTINCT
    CAST(bim360_account_id AS VARCHAR(255)) as hubId,
    display_name as hubName,
    'US' as region,
    CAST(bim360_account_id AS VARCHAR(255)) as accountId,
    start_date as createdAt,
    end_date as lastSync
FROM admin_accounts
WHERE display_name IS NOT NULL
GO

-- Create Projects view using admin_projects
IF EXISTS (SELECT * FROM sys.views WHERE name='vw_Projects')
    DROP VIEW vw_Projects
GO

CREATE VIEW vw_Projects AS
SELECT 
    CAST(id AS VARCHAR(255)) as projectId,
    CAST(bim360_account_id AS VARCHAR(255)) as hubId,
    name as projectName,
    status,
    type as projectType,
    created_at as createdAt,
    updated_at as updatedAt,
    updated_at as lastSync
FROM admin_projects
WHERE name IS NOT NULL
GO

-- Create Issues view using issues_issues
IF EXISTS (SELECT * FROM sys.views WHERE name='vw_Issues')
    DROP VIEW vw_Issues
GO

CREATE VIEW vw_Issues AS
SELECT 
    CAST(issue_id AS VARCHAR(255)) as issueId,
    CAST(bim360_project_id AS VARCHAR(255)) as projectId,
    title,
    description,
    status,
    'Normal' as priority,
    CAST(type_id AS VARCHAR(100)) as issueType,
    assignee_id as assignedTo,
    created_by as createdBy,
    created_at as createdAt,
    updated_at as updatedAt,
    due_date as dueDate,
    updated_at as lastSync
FROM issues_issues
WHERE title IS NOT NULL
GO

-- Test all views
SELECT 'Hub Count:' as Info, COUNT(*) as count FROM vw_Hubs
UNION ALL
SELECT 'Project Count:', COUNT(*) FROM vw_Projects
UNION ALL
SELECT 'Issue Count:', COUNT(*) FROM vw_Issues
GO

-- Sample data
SELECT 'Sample Hubs:' as Info, hubId, hubName FROM vw_Hubs WHERE hubName IS NOT NULL
GO

SELECT TOP 3 'Sample Projects:' as Info, projectId, projectName, status FROM vw_Projects WHERE projectName IS NOT NULL
GO