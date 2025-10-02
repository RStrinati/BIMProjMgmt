CREATE TABLE tblACCDocs (
    id INT IDENTITY(1,1) PRIMARY KEY,
    file_name NVARCHAR(510) NOT NULL,
    file_path NVARCHAR(MAX) NOT NULL,
    date_modified DATETIME NULL,
    file_type NVARCHAR(100) NULL,
    file_size_kb FLOAT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    deleted_at DATETIME NULL,
    project_id INT NOT NULL,
    CONSTRAINT FK_tblACCDocs_Projects FOREIGN KEY (project_id) REFERENCES Projects(project_id)
);
GO
