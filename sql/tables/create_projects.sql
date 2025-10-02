CREATE TABLE Projects (
    project_id INT IDENTITY(1,1) PRIMARY KEY,
    project_name NVARCHAR(510) NOT NULL,
    folder_path NVARCHAR(1000) NULL,
    ifc_folder_path NVARCHAR(1000) NULL,
    data_export_folder NVARCHAR(1000) NULL,
    start_date DATE NULL,
    end_date DATE NULL,
    status NVARCHAR(100) NULL,
    priority NVARCHAR(100) NULL,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME NULL
);
GO
