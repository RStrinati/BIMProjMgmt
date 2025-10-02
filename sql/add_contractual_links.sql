IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ContractualLinks')
BEGIN
    CREATE TABLE ContractualLinks (
        id INT IDENTITY(1,1) PRIMARY KEY,
        project_id INT NOT NULL,
        review_cycle_id INT NULL,
        bep_clause NVARCHAR(255) NOT NULL,
        billing_event NVARCHAR(255) NOT NULL,
        amount_due DECIMAL(18,2) DEFAULT 0,
        status NVARCHAR(50) DEFAULT 'Pending'
    );
END;
GO
