CREATE TABLE ProjectServices (
    service_id INT IDENTITY(1,1) PRIMARY KEY,
    project_id INT NOT NULL,
    phase NVARCHAR(200) NULL,
    service_code NVARCHAR(50) NULL,
    service_name NVARCHAR(500) NULL,
    unit_type NVARCHAR(50) NULL,
    unit_qty INT NULL,
    unit_rate DECIMAL(18,2) NULL,
    lump_sum_fee DECIMAL(18,2) NULL,
    agreed_fee DECIMAL(18,2) NULL,
    bill_rule NVARCHAR(100) NULL,
    notes NVARCHAR(MAX) NULL,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME NULL,
    CONSTRAINT FK_ProjectServices_Projects FOREIGN KEY (project_id) REFERENCES Projects(project_id)
);
GO
