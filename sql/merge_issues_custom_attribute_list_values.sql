SET XACT_ABORT ON;
BEGIN TRAN;

;WITH src_raw AS (
    SELECT 
        TRY_CONVERT(uniqueidentifier, NULLIF(LTRIM(RTRIM(s.attribute_mappings_id)), '')) AS attribute_mappings_id_guid,
        TRY_CONVERT(uniqueidentifier, NULLIF(LTRIM(RTRIM(s.bim360_account_id)), ''))    AS bim360_account_id_guid,
        TRY_CONVERT(uniqueidentifier, NULLIF(LTRIM(RTRIM(s.bim360_project_id)), ''))    AS bim360_project_id_guid,
        TRY_CONVERT(uniqueidentifier, NULLIF(LTRIM(RTRIM(s.list_id)), ''))              AS list_id_guid,
        LTRIM(RTRIM(s.list_value))                                                      AS list_value
    FROM acc_data_schema.staging.issues_custom_attribute_list_values s
),
src_valid AS (
    SELECT *
    FROM src_raw
    WHERE attribute_mappings_id_guid IS NOT NULL
      AND list_id_guid IS NOT NULL
      AND list_value <> ''
),
src_deduped AS (
    -- Keep one row per (attribute_mappings_id, list_id, list_value)
    SELECT *
    FROM (
        SELECT r.*,
               ROW_NUMBER() OVER (
                   PARTITION BY r.attribute_mappings_id_guid, r.list_id_guid, r.list_value
                   ORDER BY r.list_value ASC
               ) AS rn
        FROM src_valid r
    ) x
    WHERE rn = 1
)

MERGE acc_data_schema.dbo.issues_custom_attribute_list_values AS tgt
USING src_deduped AS src
   ON  tgt.attribute_mappings_id = src.attribute_mappings_id_guid
   AND tgt.list_id               = src.list_id_guid
   AND tgt.list_value            = src.list_value
WHEN MATCHED THEN
  UPDATE SET
      tgt.bim360_account_id = src.bim360_account_id_guid,
      tgt.bim360_project_id = src.bim360_project_id_guid
WHEN NOT MATCHED BY TARGET THEN
  INSERT (
      attribute_mappings_id,
      bim360_account_id,
      bim360_project_id,
      list_id,
      list_value
  )
  VALUES (
      src.attribute_mappings_id_guid,
      src.bim360_account_id_guid,
      src.bim360_project_id_guid,
      src.list_id_guid,
      src.list_value
  );

COMMIT;
