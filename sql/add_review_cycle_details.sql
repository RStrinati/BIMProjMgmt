IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ReviewCycleDetails')
BEGIN
    CREATE TABLE ReviewCycleDetails (
        project_id INT NOT NULL,
        cycle_id INT NOT NULL,
        construction_stage NVARCHAR(100),
        proposed_fee DECIMAL(18,2),
        assigned_users NVARCHAR(MAX),
        reviews_per_phase NVARCHAR(MAX),
        planned_start_date DATE,
        planned_completion_date DATE,
        actual_start_date DATE,
        actual_completion_date DATE,
        hold_date DATE,
        resume_date DATE,
        new_contract BIT DEFAULT 0,
        CONSTRAINT PK_ReviewCycleDetails PRIMARY KEY (project_id, cycle_id)
    );
END;
GO
