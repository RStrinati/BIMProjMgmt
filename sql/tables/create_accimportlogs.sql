CREATE TABLE ACCImportLogs (
    log_id INT IDENTITY(1,1) PRIMARY KEY,
    project_id INT NOT NULL,
    folder_name NVARCHAR(1000) NOT NULL,
    import_date DATETIME DEFAULT GETDATE(),
    summary NVARCHAR(MAX) NULL,
    CONSTRAINT FK_ACCImportLogs_Projects FOREIGN KEY (project_id) REFERENCES Projects(project_id)
);
GO
