-- MERGE for issues_issues
WITH src_deduped AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY issue_id
        ORDER BY updated_at DESC
    ) AS rn
    FROM staging.issues_issues
    WHERE issue_id IS NOT NULL
)
MERGE INTO dbo.issues_issues AS tgt
USING (SELECT * FROM src_deduped WHERE rn = 1) AS src
ON tgt.issue_id = src.issue_id
WHEN MATCHED THEN
    UPDATE SET
        bim360_account_id = src.bim360_account_id,
        bim360_project_id = src.bim360_project_id,
        display_id = src.display_id,
        title = src.title,
        description = src.description,
        type_id = src.type_id,
        subtype_id = src.subtype_id,
        status = src.status,
        assignee_id = src.assignee_id,
        assignee_type = src.assignee_type,
        due_date = src.due_date,
        location_id = src.location_id,
        location_details = src.location_details,
        linked_document_urn = src.linked_document_urn,
        owner_id = src.owner_id,
        root_cause_id = src.root_cause_id,
        root_cause_category_id = src.root_cause_category_id,
        response = src.response,
        response_by = src.response_by,
        response_at = src.response_at,
        opened_by = src.opened_by,
        opened_at = src.opened_at,
        closed_by = src.closed_by,
        closed_at = src.closed_at,
        created_by = src.created_by,
        created_at = src.created_at,
        updated_by = src.updated_by,
        updated_at = src.updated_at,
        start_date = src.start_date,
        deleted_at = src.deleted_at,
        snapshot_urn = src.snapshot_urn,
        published = src.published,
        gps_coordinates = src.gps_coordinates,
        deleted_by = src.deleted_by,
        source_load_ts = src.source_load_ts
WHEN NOT MATCHED THEN
    INSERT (issue_id, bim360_account_id, bim360_project_id, display_id, title, description, type_id, subtype_id,
            status, assignee_id, assignee_type, due_date, location_id, location_details, linked_document_urn,
            owner_id, root_cause_id, root_cause_category_id, response, response_by, response_at, opened_by,
            opened_at, closed_by, closed_at, created_by, created_at, updated_by, updated_at, start_date,
            deleted_at, snapshot_urn, published, gps_coordinates, deleted_by, source_load_ts)
    VALUES (src.issue_id, src.bim360_account_id, src.bim360_project_id, src.display_id, src.title, src.description, src.type_id, src.subtype_id,
            src.status, src.assignee_id, src.assignee_type, src.due_date, src.location_id, src.location_details, src.linked_document_urn,
            src.owner_id, src.root_cause_id, src.root_cause_category_id, src.response, src.response_by, src.response_at, src.opened_by,
            src.opened_at, src.closed_by, src.closed_at, src.created_by, src.created_at, src.updated_by, src.updated_at, src.start_date,
            src.deleted_at, src.snapshot_urn, src.published, src.gps_coordinates, src.deleted_by, src.source_load_ts);
