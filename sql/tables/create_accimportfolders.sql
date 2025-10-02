CREATE TABLE ACCImportFolders (
    project_id INT PRIMARY KEY,
    acc_folder_path NVARCHAR(1000) NOT NULL,
    last_import_date DATETIME NULL,
    CONSTRAINT FK_ACCImportFolders_Projects FOREIGN KEY (project_id) REFERENCES Projects(project_id)
);
GO
