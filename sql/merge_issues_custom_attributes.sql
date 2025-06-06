-- MERGE for issues_custom_attributes
WITH src_deduped AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY issue_id
        ORDER BY created_at DESC
    ) AS rn
    FROM staging.issues_custom_attributes
    WHERE issue_id IS NOT NULL
)
MERGE INTO dbo.issues_custom_attributes AS tgt
USING (SELECT * FROM src_deduped WHERE rn = 1) AS src
ON tgt.issue_id = src.issue_id
WHEN MATCHED THEN
    UPDATE SET
        mapped_item_type = src.mapped_item_type,
        attribute_mapping_id = src.attribute_mapping_id,
        attribute_title = src.attribute_title,
        attribute_description = src.attribute_description,
        attribute_data_type = src.attribute_data_type,
        is_required = src.is_required,
        attribute_value = src.attribute_value
WHEN NOT MATCHED THEN
    INSERT (issue_id, mapped_item_type, attribute_mapping_id, attribute_title, attribute_description, attribute_data_type, is_required, attribute_value)
    VALUES (src.issue_id, src.mapped_item_type, src.attribute_mapping_id, src.attribute_title, src.attribute_description, src.attribute_data_type, src.is_required, src.attribute_value);
