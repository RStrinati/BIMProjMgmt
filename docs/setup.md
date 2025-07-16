# Environment Setup

This project connects to a SQL Server database via ODBC. Install the Microsoft ODBC driver before installing Python dependencies.

## Install ODBC Driver

- **Windows:** Download and install the latest *ODBC Driver for SQL Server* from the [Microsoft website](https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server).
- **macOS:** `brew install msodbcsql18`
- **Linux (Debian/Ubuntu):** `sudo apt-get install msodbcsql18`

## Python Environment

Run the provided script to create a virtual environment and install the required packages:

```bash
./setup_env.sh
```

The script creates a `.venv` folder and runs `pip install -r requirements.txt` inside it.

## Required Environment Variables

Set the following variables before running the tools:

- `DB_SERVER` – SQL Server host (default `...`)
- `DB_USER` – database username (default `...`)
- `DB_PASSWORD` – database password (default `...`)
- `DB_DRIVER` – ODBC driver name (default `...`)
- `PROJECT_MGMT_DB` – default project management database (default `ProjectManagement`)
- `ACC_DB` – Autodesk Construction Cloud staging database (default `acc_data_schema`)
- `REVIT_HEALTH_DB` – Revit health check database (default `RevitHealthCheckDB`)

These variables can be stored in your shell profile or in a `.env` file loaded before execution.

## Database Schema Updates

After setting up your Python environment and environment variables, run the SQL
script to ensure the `ReviewSchedule` table includes the latest columns:

```bash
sqlcmd -S <server> -d <database> -i sql/update_review_schedule_schema.sql
```

Run this script whenever setting up a new database or upgrading from an older
version of the project.
