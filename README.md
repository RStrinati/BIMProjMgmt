# BIMProjMgmt

This project requires access to a SQL Server database. Connection details are read from environment variables so sensitive credentials do not need to be hard coded.

Set the following variables before running the tools:

- `DB_SERVER` – SQL Server host (default `...`)
- `DB_USER` – database username (default `...`)
- `DB_PASSWORD` – database password (default `...`)
- `DB_DRIVER` – ODBC driver name (default `...`)
- `PROJECT_MGMT_DB` – default project management database name (default `ProjectManagement`)
- `ACC_DB` – Autodesk Construction Cloud staging database name (default `acc_data_schema`)
- `REVIT_HEALTH_DB` – Revit health check database name (default `RevitHealthCheckDB`)

These variables can be placed in your shell profile or a `.env` file loaded before execution.

## Setup

Install a compatible ODBC driver for SQL Server (see [docs/setup.md](docs/setup.md)) and ensure the environment variables above are set. Then run:

```bash
./setup_env.sh
```

This creates a virtual environment in `.venv` and installs the Python dependencies listed in `requirements.txt`, including the Flask components used by the backend.

The requirements now include `Flask` and `Flask-Cors` for the API server.

## Database Schema

The main tables used by the application are documented in
[docs/database_schema.md](docs/database_schema.md). Consult that file for a full
list of columns if you need to create the SQL schema manually.

## Local Web Application

A simple Flask backend and React frontend are now provided.

Launch the web interface with:

```bash
python app.py
```

This command starts the Flask backend and automatically opens the React
frontend in your default browser for a basic review task manager.
