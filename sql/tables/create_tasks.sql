CREATE TABLE tasks (
    task_id INT IDENTITY(1,1) PRIMARY KEY,
    task_name NVARCHAR(510) NOT NULL,
    project_id INT NOT NULL,
    cycle_id INT NOT NULL,
    start_date DATE NULL,
    end_date DATE NULL,
    assigned_to INT NULL,
    dependencies NVARCHAR(510) NULL,
    progress DECIMAL(5,2) DEFAULT 0,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME NULL,
    CONSTRAINT FK_Tasks_Projects FOREIGN KEY (project_id) REFERENCES Projects(project_id),
    CONSTRAINT FK_Tasks_Users FOREIGN KEY (assigned_to) REFERENCES users(user_id)
);
GO
