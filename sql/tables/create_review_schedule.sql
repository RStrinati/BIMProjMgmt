CREATE TABLE ReviewSchedule (
    schedule_id INT IDENTITY(1,1) PRIMARY KEY,
    project_id INT NOT NULL,
    cycle_id INT NOT NULL,
    review_date DATE NOT NULL,
    assigned_to INT NULL,
    status NVARCHAR(100) NULL,
    is_blocked BIT DEFAULT 0,
    is_within_license_period BIT DEFAULT 1,
    manual_override BIT DEFAULT 0,
    CONSTRAINT FK_ReviewSchedule_Projects FOREIGN KEY (project_id) REFERENCES Projects(project_id),
    CONSTRAINT FK_ReviewSchedule_Parameters FOREIGN KEY (cycle_id, project_id) REFERENCES ReviewParameters(cycle_id, ProjectID),
    CONSTRAINT FK_ReviewSchedule_Users FOREIGN KEY (assigned_to) REFERENCES users(user_id)
);
GO
