-- Add an invoice reference field to service items so billing artifacts can be linked directly.
IF COL_LENGTH('ServiceItems', 'invoice_reference') IS NULL
BEGIN
    ALTER TABLE ServiceItems
        ADD invoice_reference NVARCHAR(200) NULL;
END;
