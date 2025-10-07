-- Auto-generated view with custom attributes expanded
-- Generated: analyze_custom_attributes.py
-- JSON Structure: Array of objects with 'name' and 'value' properties

CREATE OR ALTER VIEW [dbo].[vw_issues_expanded_custom_attrs] AS
SELECT 
    i.[issue_id],
    i.[display_id],
    i.[title],
    i.[status],
    i.[due_date],
    i.[description],
    i.[created_at],
    i.[closed_at],
    i.[clash_group_id],
    i.[clash_test_id],
    i.[clash_status],
    i.[clash_created_at],
    i.[clash_title],
    i.[clash_description],
    i.[latest_comment],
    i.[latest_comment_by],
    i.[latest_comment_at],
    i.[location_id],
    i.[location_name],
    i.[location_parent_id],
    i.[location_tree_name],
    i.[building_name],
    i.[level_name],
    i.[root_location],
    i.[created_week_start],
    i.[created_week_label],
    i.[closed_week_start],
    i.[closed_week_label],
    i.[raw_level],
    i.[normalized_level],
    i.[is_active_issue],
    i.[is_active_over_30_days],
    i.[is_closed_last_14_days],
    i.[is_closed_last_7_days],
    i.[is_opened_this_week],
    i.[is_closed_this_week],
    i.[assignee_display_name],
    i.[Discipline],
    i.[Company],
    i.[project_id],
    i.[project_name],
    i.[pm_project_id],
    i.[custom_attributes_json],
    i.[assignee_id],
    -- Custom Attributes Expanded
    (
        SELECT TOP 1 [value]
        FROM OPENJSON(i.custom_attributes_json)
        WITH ([name] NVARCHAR(100), [value] NVARCHAR(MAX))
        WHERE [name] = 'Priority'
    ) AS [Priority]
FROM [dbo].[vw_issues_expanded] i;
