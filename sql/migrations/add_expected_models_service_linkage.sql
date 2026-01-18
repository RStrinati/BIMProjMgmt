-- Phase 3: Service and Milestone Linkage for Quality Register
-- Link expected models to services and milestones for lifecycle integration

USE ProjectManagement;
GO

-- Add service and milestone linkage columns to ExpectedModels
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ExpectedModels' AND COLUMN_NAME = 'service_id')
BEGIN
    ALTER TABLE ExpectedModels ADD service_id INT NULL;
    PRINT 'Added service_id column';
END
ELSE
    PRINT 'service_id column already exists';

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ExpectedModels' AND COLUMN_NAME = 'milestone_id')
BEGIN
    ALTER TABLE ExpectedModels ADD milestone_id INT NULL;
    PRINT 'Added milestone_id column';
END
ELSE
    PRINT 'milestone_id column already exists';

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ExpectedModels' AND COLUMN_NAME = 'review_cycle_id')
BEGIN
    ALTER TABLE ExpectedModels ADD review_cycle_id INT NULL;
    PRINT 'Added review_cycle_id column';
END
ELSE
    PRINT 'review_cycle_id column already exists';

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ExpectedModels' AND COLUMN_NAME = 'expected_delivery_date')
BEGIN
    ALTER TABLE ExpectedModels ADD expected_delivery_date DATE NULL;
    PRINT 'Added expected_delivery_date column';
END
ELSE
    PRINT 'expected_delivery_date column already exists';

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ExpectedModels' AND COLUMN_NAME = 'actual_delivery_date')
BEGIN
    ALTER TABLE ExpectedModels ADD actual_delivery_date DATE NULL;
    PRINT 'Added actual_delivery_date column';
END
ELSE
    PRINT 'actual_delivery_date column already exists';

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ExpectedModels' AND COLUMN_NAME = 'delivery_status')
BEGIN
    ALTER TABLE ExpectedModels ADD delivery_status NVARCHAR(50) NULL; -- 'PENDING', 'ON_TRACK', 'AT_RISK', 'DELIVERED', 'LATE'
    PRINT 'Added delivery_status column';
END
ELSE
    PRINT 'delivery_status column already exists';
GO

-- Add foreign keys (if tables exist and have proper structure)
BEGIN TRY
    IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'project_services')
    BEGIN
        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS 
                       WHERE CONSTRAINT_NAME = 'FK_ExpectedModels_ServiceId')
        BEGIN
            ALTER TABLE ExpectedModels 
            ADD CONSTRAINT FK_ExpectedModels_ServiceId 
            FOREIGN KEY (service_id) REFERENCES project_services(service_id);
            PRINT 'Added FK to project_services';
        END
    END
END TRY
BEGIN CATCH
    PRINT 'Could not add FK to project_services - table may not be compatible';
END CATCH

BEGIN TRY
    IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'project_review_cycles')
    BEGIN
        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS 
                       WHERE CONSTRAINT_NAME = 'FK_ExpectedModels_ReviewCycleId')
        BEGIN
            ALTER TABLE ExpectedModels 
            ADD CONSTRAINT FK_ExpectedModels_ReviewCycleId 
            FOREIGN KEY (review_cycle_id) REFERENCES project_review_cycles(id);
            PRINT 'Added FK to project_review_cycles';
        END
    END
END TRY
BEGIN CATCH
    PRINT 'Could not add FK to project_review_cycles - table may not be compatible';
END CATCH

-- Create indexes for performance
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IDX_ExpectedModels_ServiceId')
BEGIN
    CREATE INDEX IDX_ExpectedModels_ServiceId ON ExpectedModels(service_id);
    PRINT 'Created index on service_id';
END

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IDX_ExpectedModels_ReviewCycleId')
BEGIN
    CREATE INDEX IDX_ExpectedModels_ReviewCycleId ON ExpectedModels(review_cycle_id);
    PRINT 'Created index on review_cycle_id';
END

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IDX_ExpectedModels_DeliveryStatus')
BEGIN
    CREATE INDEX IDX_ExpectedModels_DeliveryStatus ON ExpectedModels(delivery_status);
    PRINT 'Created index on delivery_status';
END

PRINT '';
PRINT '✅ Phase 3 service/milestone linkage complete';
GO
