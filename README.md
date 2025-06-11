# BIMProjMgmt

This project requires access to a SQL Server database. Connection details are read from environment variables so sensitive credentials do not need to be hard coded.

Set the following variables before running the tools:

- `DB_SERVER` – SQL Server host (default `P-NB-USER-028\SQLEXPRESS`)
- `DB_USER` – database username (default `admin02`)
- `DB_PASSWORD` – database password (default `1234`)
- `DB_DRIVER` – ODBC driver name (default `ODBC Driver 17 for SQL Server`)
- `PROJECT_MGMT_DB` – default project management database name (default `ProjectManagement`)
- `ACC_DB` – Autodesk Construction Cloud staging database name (default `acc_data_schema`)
- `REVIT_HEALTH_DB` – Revit health check database name (default `RevitHealthCheckDB`)

These variables can be placed in your shell profile or a `.env` file loaded before execution.
