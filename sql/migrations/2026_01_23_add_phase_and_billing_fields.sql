-- Adds phase and billing fields to ServiceReviews and ServiceItems
-- Safe to run multiple times; guards against existing columns.

-- ServiceReviews: phase + billing
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE name = 'phase' AND object_id = OBJECT_ID('ServiceReviews'))
BEGIN
    ALTER TABLE ServiceReviews ADD phase NVARCHAR(120) NULL;
END;

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE name = 'fee_amount' AND object_id = OBJECT_ID('ServiceReviews'))
BEGIN
    ALTER TABLE ServiceReviews ADD fee_amount DECIMAL(18,2) NULL;
END;

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE name = 'billed_amount' AND object_id = OBJECT_ID('ServiceReviews'))
BEGIN
    ALTER TABLE ServiceReviews ADD billed_amount DECIMAL(18,2) NULL;
END;

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE name = 'invoice_status' AND object_id = OBJECT_ID('ServiceReviews'))
BEGIN
    ALTER TABLE ServiceReviews ADD invoice_status NVARCHAR(32) NULL; -- unbilled | invoiced | paid
END;

-- ServiceItems: phase + billing
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE name = 'phase' AND object_id = OBJECT_ID('ServiceItems'))
BEGIN
    ALTER TABLE ServiceItems ADD phase NVARCHAR(120) NULL;
END;

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE name = 'fee_amount' AND object_id = OBJECT_ID('ServiceItems'))
BEGIN
    ALTER TABLE ServiceItems ADD fee_amount DECIMAL(18,2) NULL;
END;

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE name = 'billed_amount' AND object_id = OBJECT_ID('ServiceItems'))
BEGIN
    ALTER TABLE ServiceItems ADD billed_amount DECIMAL(18,2) NULL;
END;

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE name = 'invoice_status' AND object_id = OBJECT_ID('ServiceItems'))
BEGIN
    ALTER TABLE ServiceItems ADD invoice_status NVARCHAR(32) NULL; -- unbilled | invoiced | paid
END;

-- Seed defaults for existing rows
UPDATE sr
SET
    sr.phase = COALESCE(sr.phase, ps.phase),
    sr.invoice_status = COALESCE(sr.invoice_status, CASE WHEN sr.is_billed = 1 THEN 'invoiced' ELSE 'unbilled' END),
    sr.fee_amount = COALESCE(sr.fee_amount, sr.billing_amount),
    sr.billed_amount = COALESCE(sr.billed_amount, CASE WHEN sr.is_billed = 1 THEN sr.billing_amount ELSE 0 END)
FROM ServiceReviews sr
LEFT JOIN ProjectServices ps ON sr.service_id = ps.service_id;

UPDATE si
SET
    si.phase = COALESCE(si.phase, ps.phase),
    si.invoice_status = COALESCE(si.invoice_status, CASE WHEN si.is_billed = 1 THEN 'invoiced' ELSE 'unbilled' END),
    si.fee_amount = COALESCE(si.fee_amount, 0),
    si.billed_amount = COALESCE(si.billed_amount, CASE WHEN si.is_billed = 1 THEN COALESCE(si.fee_amount, 0) ELSE 0 END)
FROM ServiceItems si
LEFT JOIN ProjectServices ps ON si.service_id = ps.service_id;
