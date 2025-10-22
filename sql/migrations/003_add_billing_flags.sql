-- Adds explicit billing flags to service reviews and service items.

ALTER TABLE ServiceReviews
    ADD is_billed BIT NOT NULL CONSTRAINT DF_ServiceReviews_IsBilled DEFAULT 0;

ALTER TABLE ServiceItems
    ADD is_billed BIT NOT NULL CONSTRAINT DF_ServiceItems_IsBilled DEFAULT 0;

-- Align existing completed records with billed status.
UPDATE ServiceReviews
SET is_billed = CASE WHEN LOWER(ISNULL(status, '')) = 'completed' THEN 1 ELSE 0 END;

UPDATE ServiceItems
SET is_billed = CASE WHEN LOWER(ISNULL(status, '')) = 'completed' THEN 1 ELSE 0 END;
