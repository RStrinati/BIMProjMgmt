CREATE TABLE ReviewParameters (
    ParameterID INT IDENTITY(1,1) PRIMARY KEY,
    ProjectID INT NOT NULL,
    ReviewStartDate DATE NOT NULL,
    NumberOfReviews INT NOT NULL,
    ReviewFrequency INT NOT NULL,
    LicenseStartDate DATE NULL,
    LicenseEndDate DATE NULL,
    cycle_id INT NOT NULL,
    CONSTRAINT FK_ReviewParameters_Projects FOREIGN KEY (ProjectID) REFERENCES Projects(project_id)
);
GO
