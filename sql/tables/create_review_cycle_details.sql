CREATE TABLE ReviewCycleDetails (
    cycle_detail_id INT IDENTITY(1,1) PRIMARY KEY,
    project_id INT NOT NULL,
    cycle_id INT NOT NULL,
    construction_stage NVARCHAR(200) NULL,
    proposed_fee DECIMAL(18,2) NULL,
    assigned_users NVARCHAR(255) NULL,
    reviews_per_phase INT NULL,
    planned_start_date DATE NULL,
    planned_completion_date DATE NULL,
    actual_start_date DATE NULL,
    actual_completion_date DATE NULL,
    hold_date DATE NULL,
    resume_date DATE NULL,
    new_contract BIT DEFAULT 0,
    last_updated DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_ReviewCycleDetails_Projects FOREIGN KEY (project_id) REFERENCES Projects(project_id),
    CONSTRAINT FK_ReviewCycleDetails_Parameters FOREIGN KEY (cycle_id, project_id) REFERENCES ReviewParameters(cycle_id, ProjectID)
);
GO
