SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

ALTER VIEW [dbo].[vw_issues_expanded] AS

WITH 
-- Rank user roles
RankedRoles AS (
    SELECT *
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY project_id, user_id
                   ORDER BY role_assigned_at DESC
               ) AS rn
        FROM dbo.vw_project_user_company_roles
    ) sub
    WHERE rn = 1
),

-- Rank company roles
RankedCompanyRoles AS (
    SELECT *
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY project_id, company_id
                   ORDER BY role_assigned_at DESC
               ) AS rn
        FROM dbo.vw_project_user_company_roles
        WHERE company_id IS NOT NULL
    ) sub
    WHERE rn = 1
),

-- Latest comment per issue
LatestComment AS (
    SELECT *
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY issue_id
                   ORDER BY created_at DESC
               ) AS rn
        FROM acc_data_schema.dbo.issues_comments
    ) sub
    WHERE rn = 1
),

-- Location hierarchy
LocationHierarchy AS (
    SELECT
        child.id   AS location_id,
        child.name AS level_name,
        parent.id  AS parent_id,
        parent.name AS building_name,
        grandparent.name AS root_location
    FROM acc_data_schema.dbo.locations_nodes child
    LEFT JOIN acc_data_schema.dbo.locations_nodes parent
        ON child.parent_id = parent.id
    LEFT JOIN acc_data_schema.dbo.locations_nodes grandparent
        ON parent.parent_id = grandparent.id
),

/* -----------------------------------------------------------
   Project → PM mapping with aliases + normalization + fallback
   normalize(x) := UPPER(REPLACE(REPLACE(REPLACE(REPLACE(LTRIM(RTRIM(x)),' ',''),'-',''),'_',''),'.',''))
   ----------------------------------------------------------- */
ProjectNames AS (
    SELECT dp.pm_project_id, dp.project_name AS match_name, 1 AS priority
    FROM ProjectManagement.dbo.vw_dim_projects dp
    UNION ALL
    SELECT pa.pm_project_id, pa.alias_name, 2 AS priority
    FROM ProjectManagement.dbo.project_aliases pa
),
ProjectNamesNorm AS (
    SELECT
        pm_project_id,
        priority,
        match_name,
        UPPER(REPLACE(REPLACE(REPLACE(REPLACE(LTRIM(RTRIM(match_name)),' ',''),'-',''),'_',''),'.',''))
            COLLATE DATABASE_DEFAULT AS n_match_name
    FROM ProjectNames
),
AdminProjectsNorm AS (
    SELECT
        ap.id   AS acc_project_id,
        ap.name AS acc_project_name,
        UPPER(REPLACE(REPLACE(REPLACE(REPLACE(LTRIM(RTRIM(ap.name)),' ',''),'-',''),'_',''),'.',''))
            COLLATE DATABASE_DEFAULT AS n_acc_name
    FROM acc_data_schema.dbo.admin_projects ap
),
ProjectMap AS (
    SELECT
        apn.acc_project_id,
        apn.acc_project_name,
        best.pm_project_id
    FROM AdminProjectsNorm apn
    OUTER APPLY (
        SELECT TOP (1) x.pm_project_id, x.score, x.priority
        FROM (
            SELECT pnn.pm_project_id, 1 AS score, pnn.priority
            FROM ProjectNamesNorm pnn
            WHERE pnn.n_match_name = apn.n_acc_name

            UNION ALL
            SELECT pnn.pm_project_id, 2 AS score, pnn.priority
            FROM ProjectNamesNorm pnn
            WHERE apn.n_acc_name LIKE pnn.n_match_name + '%'

            UNION ALL
            SELECT pnn.pm_project_id, 3 AS score, pnn.priority
            FROM ProjectNamesNorm pnn
            WHERE pnn.n_match_name LIKE apn.n_acc_name + '%'
        ) x
        ORDER BY x.score, x.priority, x.pm_project_id
    ) best
),

/* -------------------------
   Custom attributes resolver
   ------------------------- */
-- If your list values are only in staging, change the next CTE to: acc_data_schema.staging.issues_custom_attribute_list_values
ListValues AS (
    SELECT
        attribute_mappings_id,
        bim360_account_id,
        bim360_project_id,
        list_id,
        list_value
    FROM acc_data_schema.dbo.issues_custom_attribute_list_values
),
AttrBase AS (
    SELECT
        ica.issue_id,
        ica.bim360_project_id,
        ica.bim360_account_id,
        ica.attribute_mapping_id,
        COALESCE(ica.attribute_title, icam.title) AS attribute_title,
        COALESCE(ica.attribute_data_type, icam.data_type) AS attribute_data_type,
        ica.attribute_value,
        lv.list_value,
        COALESCE(lv.list_value, ica.attribute_value) AS attribute_display_value,
        icam.is_required,
        ica.created_at AS attribute_created_at
    FROM acc_data_schema.dbo.issues_custom_attributes ica
    LEFT JOIN acc_data_schema.dbo.issues_custom_attributes_mappings icam
      ON icam.id = ica.attribute_mapping_id
     AND icam.bim360_project_id = ica.bim360_project_id
     AND icam.bim360_account_id = ica.bim360_account_id
    LEFT JOIN ListValues lv
      ON lv.attribute_mappings_id = ica.attribute_mapping_id
     AND lv.list_id = ica.attribute_value
     AND lv.bim360_project_id = ica.bim360_project_id
     AND lv.bim360_account_id = ica.bim360_account_id
)

SELECT
    i.issue_id,
    i.display_id,
    i.title,
    i.status,
    i.due_date,
    i.description,
    i.created_at,
    i.closed_at,

    -- Clash data
    cag.clash_group_id,
    cag.clash_test_id,
    cag.status AS clash_status,
    cag.created_at AS clash_created_at,
    cag.title AS clash_title,
    cag.description AS clash_description,

    ic.comment_body AS latest_comment,
    ic.created_by   AS latest_comment_by,
    ic.created_at   AS latest_comment_at,

    -- Location info
    i.location_id,
    ln.name AS location_name,
    ln.parent_id AS location_parent_id,
    lt.name AS location_tree_name,
    lh.building_name,
    lh.level_name,
    lh.root_location,

    -- Weekly tracking
    DATEADD(DAY, 1 - DATEPART(WEEKDAY, i.created_at), CAST(i.created_at AS DATE)) AS created_week_start,
    FORMAT(i.created_at, 'yyyy') + '-W' + RIGHT('0' + CAST(DATEPART(WEEK, i.created_at) AS VARCHAR), 2) AS created_week_label,

    CASE 
        WHEN i.closed_at IS NOT NULL THEN DATEADD(DAY, 1 - DATEPART(WEEKDAY, i.closed_at), CAST(i.closed_at AS DATE))
        ELSE NULL 
    END AS closed_week_start,

    CASE 
        WHEN i.closed_at IS NOT NULL THEN FORMAT(i.closed_at, 'yyyy') + '-W' + RIGHT('0' + CAST(DATEPART(WEEK, i.closed_at) AS VARCHAR), 2)
        ELSE NULL 
    END AS closed_week_label,

    -- Level details
    i.location_details AS raw_level,
    CASE WHEN i.location_details IN ('R0','R1','R2','RF') THEN i.location_details ELSE 'R0' END AS normalized_level,

    -- Status indicators
    CASE WHEN i.closed_at IS NULL THEN 1 ELSE 0 END AS is_active_issue,
    CASE WHEN i.closed_at IS NULL AND DATEDIFF(DAY, i.created_at, GETDATE()) > 30 THEN 1 ELSE 0 END AS is_active_over_30_days,
    CASE WHEN i.closed_at IS NOT NULL AND i.closed_at >= DATEADD(DAY, -14, GETDATE()) THEN 1 ELSE 0 END AS is_closed_last_14_days,
    CASE WHEN i.closed_at IS NOT NULL AND i.closed_at >= DATEADD(DAY, -7, GETDATE()) THEN 1 ELSE 0 END AS is_closed_last_7_days,
    CASE WHEN DATEDIFF(WEEK, i.created_at, GETDATE()) = 0 THEN 1 ELSE 0 END AS is_opened_this_week,
    CASE WHEN i.closed_at IS NOT NULL AND DATEDIFF(WEEK, i.closed_at, GETDATE()) = 0 THEN 1 ELSE 0 END AS is_closed_this_week,

    -- Assignee display (user/company)
    CASE 
        WHEN au.id IS NOT NULL THEN au.name
        WHEN ac.id IS NOT NULL THEN ac.name
        ELSE 'Unknown Assignee'
    END AS assignee_display_name,

    -- Role / discipline
    CASE 
        WHEN rr.role_name  IS NOT NULL THEN rr.role_name
        WHEN rcr.role_name IS NOT NULL THEN rcr.role_name
        ELSE NULL
    END AS Discipline,

    -- Company
    CASE 
        WHEN rr.company_name IS NOT NULL THEN rr.company_name
        WHEN ac.name        IS NOT NULL THEN ac.name
        ELSE NULL
    END AS Company,

    -- ACC project info
    ap.id   AS project_id,
    ap.name AS project_name,

    -- PM dimension key
    pm.pm_project_id,

    -- 🔹 Custom attributes as JSON array [{name,type,value,is_required,created_at}, ...]
    ca.custom_attributes_json,

    -- For troubleshooting
    i.assignee_id,

    -- 🔹 Custom Attributes Expanded - All 6 custom attributes extracted from JSON
    -- Building Level: In-ground, Level 00, Level 00 Mezz, Roof Level
    (
        SELECT TOP 1 [value]
        FROM OPENJSON(ca.custom_attributes_json)
        WITH ([name] NVARCHAR(100), [value] NVARCHAR(MAX))
        WHERE [name] = 'Building Level'
    ) AS [Building_Level],
    
    -- Clash Level: L1-Critical, L2-Important, L3-Significant, L4-Minor
    (
        SELECT TOP 1 [value]
        FROM OPENJSON(ca.custom_attributes_json)
        WITH ([name] NVARCHAR(100), [value] NVARCHAR(MAX))
        WHERE [name] = 'Clash Level'
    ) AS [Clash_Level],
    
    -- Location: Admin, Fire Pump Building, Gen Yard, MV Room, ROMP 01-04, etc.
    (
        SELECT TOP 1 [value]
        FROM OPENJSON(ca.custom_attributes_json)
        WITH ([name] NVARCHAR(100), [value] NVARCHAR(MAX))
        WHERE [name] = 'Location'
    ) AS [Location],
    
    -- Location 01: Same values as Location but used in different project
    (
        SELECT TOP 1 [value]
        FROM OPENJSON(ca.custom_attributes_json)
        WITH ([name] NVARCHAR(100), [value] NVARCHAR(MAX))
        WHERE [name] = 'Location 01'
    ) AS [Location_01],
    
    -- Phase: PHASE 01, PHASE 02, PHASE 03, PHASE 04
    (
        SELECT TOP 1 [value]
        FROM OPENJSON(ca.custom_attributes_json)
        WITH ([name] NVARCHAR(100), [value] NVARCHAR(MAX))
        WHERE [name] = 'Phase'
    ) AS [Phase],
    
    -- Priority: Blocker, Critical, Major, Minor, Trivial (SINSW project only)
    (
        SELECT TOP 1 [value]
        FROM OPENJSON(ca.custom_attributes_json)
        WITH ([name] NVARCHAR(100), [value] NVARCHAR(MAX))
        WHERE [name] = 'Priority'
    ) AS [Priority]

FROM acc_data_schema.dbo.issues_issues i

-- Assignee user
LEFT JOIN acc_data_schema.dbo.admin_users au 
    ON LTRIM(RTRIM(au.autodesk_id)) = LTRIM(RTRIM(i.assignee_id))

-- User role
LEFT JOIN RankedRoles rr 
    ON rr.user_id = au.id 
   AND rr.project_id = i.bim360_project_id

-- Assignee company
LEFT JOIN acc_data_schema.dbo.admin_project_companies apc 
    ON LTRIM(RTRIM(apc.company_oxygen_id)) = LTRIM(RTRIM(i.assignee_id))
   AND apc.project_id = i.bim360_project_id

LEFT JOIN acc_data_schema.dbo.admin_companies ac 
    ON ac.id = apc.company_id

-- Company-level role
LEFT JOIN RankedCompanyRoles rcr 
    ON rcr.project_id = i.bim360_project_id 
   AND rcr.company_id = ac.id

-- Project info (ACC)
LEFT JOIN acc_data_schema.dbo.admin_projects ap 
    ON ap.id = i.bim360_project_id

-- Clash group info
LEFT JOIN acc_data_schema.dbo.clashes_assigned_clash_group cag 
    ON cag.issue_id = i.issue_id 
   AND cag.bim360_project_id = i.bim360_project_id

-- Latest comment
LEFT JOIN LatestComment ic
    ON ic.issue_id = i.issue_id

-- Location info
LEFT JOIN acc_data_schema.dbo.locations_nodes ln
    ON ln.id = i.location_id AND ln.bim360_project_id = i.bim360_project_id

LEFT JOIN acc_data_schema.dbo.locations_trees lt
    ON lt.id = ln.tree_id AND lt.bim360_project_id = i.bim360_project_id

-- Location hierarchy
LEFT JOIN LocationHierarchy lh
    ON lh.location_id = i.location_id

-- PM project mapping
LEFT JOIN ProjectMap pm
    ON pm.acc_project_id = i.bim360_project_id

-- Build JSON of custom attributes for each issue
OUTER APPLY (
    SELECT
        (
            SELECT 
                ab.attribute_title      AS [name],
                ab.attribute_data_type  AS [type],
                ab.attribute_display_value AS [value],
                ab.is_required          AS [is_required],
                ab.attribute_created_at AS [created_at]
            FROM AttrBase ab
            WHERE ab.issue_id = i.issue_id
            FOR JSON PATH
        ) AS custom_attributes_json
) ca

GO
