SET NOCOUNT ON;

DECLARE @Results TABLE (
    ObjectType NVARCHAR(50),
    ObjectName NVARCHAR(256),
    Status NVARCHAR(10),
    Details NVARCHAR(4000)
);

DECLARE @RequiredTables TABLE (TableName NVARCHAR(128));
INSERT INTO @RequiredTables (TableName)
VALUES
    ('Bids'),
    ('BidSections'),
    ('BidScopeItems'),
    ('BidProgramStages'),
    ('BidBillingSchedule'),
    ('BidVariations');

INSERT INTO @Results (ObjectType, ObjectName, Status, Details)
SELECT
    'TABLE',
    rt.TableName,
    CASE WHEN t.TABLE_NAME IS NULL THEN 'FAIL' ELSE 'PASS' END,
    CASE WHEN t.TABLE_NAME IS NULL THEN 'Missing table in dbo schema.' ELSE 'Table exists.' END
FROM @RequiredTables rt
LEFT JOIN INFORMATION_SCHEMA.TABLES t
    ON t.TABLE_SCHEMA = 'dbo'
   AND t.TABLE_NAME = rt.TableName;

DECLARE @RequiredColumns TABLE (TableName NVARCHAR(128), ColumnName NVARCHAR(128));
INSERT INTO @RequiredColumns (TableName, ColumnName)
VALUES
    ('Bids', 'bid_id'),
    ('Bids', 'project_id'),
    ('Bids', 'client_id'),
    ('Bids', 'bid_name'),
    ('Bids', 'bid_type'),
    ('Bids', 'status'),
    ('Bids', 'probability'),
    ('Bids', 'owner_user_id'),
    ('Bids', 'currency_code'),
    ('Bids', 'stage_framework'),
    ('Bids', 'validity_days'),
    ('Bids', 'gst_included'),
    ('Bids', 'pi_notes'),
    ('Bids', 'created_at'),
    ('Bids', 'updated_at'),
    ('BidSections', 'bid_section_id'),
    ('BidSections', 'bid_id'),
    ('BidSections', 'section_key'),
    ('BidSections', 'content_json'),
    ('BidSections', 'sort_order'),
    ('BidScopeItems', 'scope_item_id'),
    ('BidScopeItems', 'bid_id'),
    ('BidScopeItems', 'service_code'),
    ('BidScopeItems', 'title'),
    ('BidScopeItems', 'description'),
    ('BidScopeItems', 'stage_name'),
    ('BidScopeItems', 'deliverables_json'),
    ('BidScopeItems', 'included_qty'),
    ('BidScopeItems', 'unit'),
    ('BidScopeItems', 'unit_rate'),
    ('BidScopeItems', 'lump_sum'),
    ('BidScopeItems', 'is_optional'),
    ('BidScopeItems', 'option_group'),
    ('BidScopeItems', 'sort_order'),
    ('BidProgramStages', 'program_stage_id'),
    ('BidProgramStages', 'bid_id'),
    ('BidProgramStages', 'stage_name'),
    ('BidProgramStages', 'planned_start'),
    ('BidProgramStages', 'planned_end'),
    ('BidProgramStages', 'cadence'),
    ('BidProgramStages', 'cycles_planned'),
    ('BidProgramStages', 'sort_order'),
    ('BidBillingSchedule', 'billing_line_id'),
    ('BidBillingSchedule', 'bid_id'),
    ('BidBillingSchedule', 'period_start'),
    ('BidBillingSchedule', 'period_end'),
    ('BidBillingSchedule', 'amount'),
    ('BidBillingSchedule', 'notes'),
    ('BidBillingSchedule', 'sort_order'),
    ('BidVariations', 'variation_id'),
    ('BidVariations', 'project_id'),
    ('BidVariations', 'bid_id'),
    ('BidVariations', 'title'),
    ('BidVariations', 'description'),
    ('BidVariations', 'baseline_contract_value'),
    ('BidVariations', 'remaining_value'),
    ('BidVariations', 'proposed_change_value'),
    ('BidVariations', 'status'),
    ('BidVariations', 'created_at'),
    ('BidVariations', 'updated_at');

INSERT INTO @Results (ObjectType, ObjectName, Status, Details)
SELECT
    'COLUMN',
    rc.TableName + '.' + rc.ColumnName,
    CASE WHEN c.COLUMN_NAME IS NULL THEN 'FAIL' ELSE 'PASS' END,
    CASE WHEN c.COLUMN_NAME IS NULL THEN 'Missing column.' ELSE 'Column exists.' END
FROM @RequiredColumns rc
LEFT JOIN INFORMATION_SCHEMA.COLUMNS c
    ON c.TABLE_SCHEMA = 'dbo'
   AND c.TABLE_NAME = rc.TableName
   AND c.COLUMN_NAME = rc.ColumnName;

DECLARE @FkChecks TABLE (
    FkTable NVARCHAR(128),
    FkColumn NVARCHAR(128),
    PkTable NVARCHAR(128),
    PkColumn NVARCHAR(128)
);

INSERT INTO @FkChecks (FkTable, FkColumn, PkTable, PkColumn)
VALUES
    ('Bids', 'project_id', 'Projects', 'project_id'),
    ('Bids', 'client_id', 'Clients', 'client_id'),
    ('Bids', 'owner_user_id', 'Users', 'user_id'),
    ('BidSections', 'bid_id', 'Bids', 'bid_id'),
    ('BidScopeItems', 'bid_id', 'Bids', 'bid_id'),
    ('BidProgramStages', 'bid_id', 'Bids', 'bid_id'),
    ('BidBillingSchedule', 'bid_id', 'Bids', 'bid_id'),
    ('BidVariations', 'project_id', 'Projects', 'project_id'),
    ('BidVariations', 'bid_id', 'Bids', 'bid_id');

INSERT INTO @Results (ObjectType, ObjectName, Status, Details)
SELECT
    'FK-DATATYPE',
    fk.FkTable + '.' + fk.FkColumn + ' -> ' + fk.PkTable + '.' + fk.PkColumn,
    CASE
        WHEN fk_col.COLUMN_NAME IS NULL THEN 'FAIL'
        WHEN pk_col.COLUMN_NAME IS NULL THEN 'FAIL'
        WHEN fk_col.DATA_TYPE = pk_col.DATA_TYPE
             AND ISNULL(fk_col.CHARACTER_MAXIMUM_LENGTH, -1) = ISNULL(pk_col.CHARACTER_MAXIMUM_LENGTH, -1)
             AND ISNULL(fk_col.NUMERIC_PRECISION, -1) = ISNULL(pk_col.NUMERIC_PRECISION, -1)
             AND ISNULL(fk_col.NUMERIC_SCALE, -1) = ISNULL(pk_col.NUMERIC_SCALE, -1)
        THEN 'PASS'
        ELSE 'FAIL'
    END,
    CASE
        WHEN fk_col.COLUMN_NAME IS NULL THEN 'Missing FK column or table.'
        WHEN pk_col.COLUMN_NAME IS NULL THEN 'Missing PK column or table.'
        WHEN fk_col.DATA_TYPE = pk_col.DATA_TYPE
             AND ISNULL(fk_col.CHARACTER_MAXIMUM_LENGTH, -1) = ISNULL(pk_col.CHARACTER_MAXIMUM_LENGTH, -1)
             AND ISNULL(fk_col.NUMERIC_PRECISION, -1) = ISNULL(pk_col.NUMERIC_PRECISION, -1)
             AND ISNULL(fk_col.NUMERIC_SCALE, -1) = ISNULL(pk_col.NUMERIC_SCALE, -1)
        THEN 'Datatype matches.'
        ELSE 'Datatype mismatch: FK=' + fk_col.DATA_TYPE + ' PK=' + pk_col.DATA_TYPE
    END
FROM @FkChecks fk
LEFT JOIN INFORMATION_SCHEMA.COLUMNS fk_col
    ON fk_col.TABLE_SCHEMA = 'dbo'
   AND fk_col.TABLE_NAME = fk.FkTable
   AND fk_col.COLUMN_NAME = fk.FkColumn
LEFT JOIN INFORMATION_SCHEMA.COLUMNS pk_col
    ON pk_col.TABLE_SCHEMA = 'dbo'
   AND pk_col.TABLE_NAME = fk.PkTable
   AND pk_col.COLUMN_NAME = fk.PkColumn;

SELECT ObjectType, ObjectName, Status, Details
FROM @Results
ORDER BY
    CASE ObjectType
        WHEN 'TABLE' THEN 1
        WHEN 'COLUMN' THEN 2
        ELSE 3
    END,
    ObjectName;
