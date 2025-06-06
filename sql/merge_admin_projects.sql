WITH src_deduped AS (
    SELECT *, 
           ROW_NUMBER() OVER (PARTITION BY id ORDER BY updated_at DESC) AS rn
    FROM staging.admin_projects
    WHERE id IS NOT NULL
)

MERGE INTO dbo.admin_projects AS tgt
USING (SELECT * FROM src_deduped WHERE rn = 1) AS src
ON tgt.id = src.id

WHEN MATCHED THEN
    UPDATE SET
        bim360_account_id = src.bim360_account_id,
        name = src.name,
        start_date = src.start_date,
        end_date = src.end_date,
        type = src.type,
        value = src.value,
        currency = src.currency,
        status = src.status,
        job_number = src.job_number,
        address_line1 = src.address_line1,
        address_line2 = src.address_line2,
        city = src.city,
        state_or_province = src.state_or_province,
        postal_code = src.postal_code,
        country = src.country,
        timezone = src.timezone,
        construction_type = src.construction_type,
        contract_type = src.contract_type,
        business_unit_id = src.business_unit_id,
        last_sign_in = src.last_sign_in,
        created_at = src.created_at,
        acc_project = src.acc_project,
        latitude = src.latitude,
        longitude = src.longitude,
        updated_at = src.updated_at,
        status_reason = src.status_reason,
        total_member_size = src.total_member_size,
        total_company_size = src.total_company_size,
        classification = src.classification

WHEN NOT MATCHED THEN
    INSERT (
        id, bim360_account_id, name, start_date, end_date, type, value, currency,
        status, job_number, address_line1, address_line2, city, state_or_province, postal_code, 
        country, timezone, construction_type, contract_type, business_unit_id, last_sign_in,
        created_at, acc_project, latitude, longitude, updated_at, status_reason, 
        total_member_size, total_company_size, classification
    )
    VALUES (
        src.id, src.bim360_account_id, src.name, src.start_date, src.end_date, src.type, src.value, src.currency,
        src.status, src.job_number, src.address_line1, src.address_line2, src.city, src.state_or_province, src.postal_code, 
        src.country, src.timezone, src.construction_type, src.contract_type, src.business_unit_id, src.last_sign_in,
        src.created_at, src.acc_project, src.latitude, src.longitude, src.updated_at, src.status_reason, 
        src.total_member_size, src.total_company_size, src.classification
    );
