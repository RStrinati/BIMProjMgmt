# BIM Project Management System - AI Agent Instructions

## Architecture Overview

This is a **BIM (Building Information Modeling) project management system** with a **React-based web application** managing construction project reviews, scheduling, and billing workflows.

### Core Components
- **Frontend**: React + TypeScript SPA (`frontend/`) with Material-UI components, Vite bundler, React Router, and React Query
- **Backend**: Flask API (`backend/app.py`) serving REST endpoints to the web client
- **Database**: SQL Server with 3 databases:
  - `ProjectManagement` - Main project/review data
  - `acc_data_schema` - Autodesk Construction Cloud imports
  - `RevitHealthCheckDB` - Revit model health data
- **Data Access**: `database.py` with pyodbc connections
- **Configuration**: Environment variables via `config.py`

### Key Data Flows
1. **Project Setup** → **Review Cycles** → **Task Assignment** → **Billing Claims**
2. **External Data Imports**: ACC ZIP files, Revit health checks, IFC models
3. **Review Management**: Multi-stage construction reviews with scheduling and deliverables

## Critical Developer Workflows

### Database Setup & Schema Management
```bash
# Always run schema check before development
python check_schema.py --autofix --update-constants

# Environment variables required (set in shell or .env):
# DB_SERVER, DB_USER, DB_PASSWORD, DB_DRIVER
# PROJECT_MGMT_DB, ACC_DB, REVIT_HEALTH_DB
```

### Application Launch
```bash
# Backend API (Flask)
cd backend
python app.py
# Runs on http://localhost:5000

# Frontend (React + Vite dev server)
cd frontend
npm install
npm run dev
# Runs on http://localhost:5173
```

### Database Connection Pattern
```python
# Use schema constants, never hardcode table/column names
from constants import schema as S
cursor.execute(f"SELECT {S.Projects.ID}, {S.Projects.NAME} FROM {S.Projects.TABLE}")
```

## Project-Specific Conventions

### File Organization Rules
- **Tests**: All test files MUST be placed in the `tests/` directory
- **Tools**: All analysis, debugging, and utility scripts MUST be placed in the `tools/` directory  
- **Services**: Business logic services MUST be placed in the `services/` directory
- **UI Components**: Individual UI components MUST be placed in the `ui/` directory
- **Handlers**: Data import/export handlers MUST be placed in the `handlers/` directory
- **Constants**: Schema and configuration constants MUST be placed in the `constants/` directory
- **Import Paths**: Files in subdirectories MUST use proper parent directory imports:
  ```python
  # For files in tests/, tools/, services/, etc.
  import sys
  import os
  sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
  ```

**CRITICAL**: A clean and organised file system is imperative to this tool. Never place test files, analysis scripts, or utilities in the root directory.

### Schema Constants Pattern
- **Always** import from `constants/schema.py` for table/column references
- **Never** use string literals for database identifiers
- Example: `S.Projects.TABLE`, `S.ReviewSchedule.ASSIGNED_TO`

### Database Connection Management
```python
# Always use context managers or explicit close()
conn = connect_to_db()
try:
    cursor = conn.cursor()
    # ... operations ...
    conn.commit()
finally:
    conn.close()
```

### Error Handling
- Database operations: Check `conn is None` before proceeding
- API endpoints: Return JSON error responses with appropriate HTTP codes
- Frontend: Use React Query for error states and retry logic
- Log errors with context for debugging

### Import Organization
- Database functions in `database.py`
- Business logic services in dedicated modules (`review_management_service.py`)
- API routes in `backend/app.py`
- Configuration in `config.py`
- React components in `frontend/src/components/`
- API client functions in `frontend/src/api/`

## Integration Points

### External Data Sources
- **ACC (Autodesk Construction Cloud)**: Issues import via ZIP files → `acc_data_schema.dbo.vw_issues_expanded_pm`
- **Revit Health**: Model analysis data → `RevitHealthCheckDB`
- **IFC Models**: Building geometry via `ifcopenshell` library

### Cross-Database Queries
- Use `connect_to_db(db_name)` to switch between databases
- Default database is `PROJECT_MGMT_DB` (ProjectManagement)
- Import handlers: `acc_handler.py`, `rvt_health_importer.py`, `process_ifc.py`

## Common Patterns & Gotchas

### Review Cycle Management
- Reviews are organized in **cycles** within **stages** within **projects**
- Each cycle has **planned vs actual** dates, **status tracking**, and **billing integration**
- Use `ReviewManagementService` class for complex review operations

### Date Handling
- Use `datetime` objects, convert to string for SQL: `date.strftime('%Y-%m-%d')`
- Database expects `DATE`/`DATETIME2` formats
- Frontend uses HTML5 date inputs and ISO 8601 format

### React Frontend State Management
- React Query (`@tanstack/react-query`) for server state
- Local component state with React hooks (`useState`, `useEffect`)
- Material-UI (`@mui/material`) for UI components
- React Router for navigation
- Axios for HTTP requests

### API Communication
- Backend Flask API at `http://localhost:5000`
- Frontend dev server at `http://localhost:5173`
- CORS enabled for local development
- RESTful endpoints with JSON payloads
- Error responses with appropriate HTTP status codes

### Testing Approach
- Database state verification: `check_database_state.py`
- Schema validation: `check_schema.py`
- Integration tests in `tests/` directory
- Run `python -m pytest tests/` for automated testing

## File Organization Reference

### Key Files by Function
- `backend/app.py` - Flask API endpoints and application server
- `database.py` - All database operations
- `review_management_service.py` - Complex review business logic
- `config.py` - Environment configuration
- `constants/schema.py` - Database schema constants
- `frontend/src/App.tsx` - React application root
- `frontend/src/main.tsx` - React application entry point
- `frontend/src/pages/` - Page components for routing
- `frontend/src/components/` - Reusable React components
- `frontend/src/api/` - API client functions

### Data Import Handlers
- `acc_handler.py` - ACC data processing
- `rvt_health_importer.py` - Revit health data
- `ideate_health_exporter.py` - Health data export
- `process_ifc.py` - IFC model processing

### Utility Scripts
- `check_schema.py` - Schema validation and auto-fix
- `verify_schema.py` - Schema verification
- `debug_*.py` - Various debugging tools

## Development Stack

### Backend Technologies
- **Python 3.12+** - Core application language
- **Flask** - REST API web framework
- **pyodbc** - SQL Server database connectivity
- **Flask-CORS** - Cross-origin resource sharing

### Frontend Technologies
- **React 18.2+** - UI library
- **TypeScript 5.2+** - Type-safe JavaScript
- **Vite 5.0** - Build tool and dev server
- **Material-UI 5.14+** - Component library
- **React Router 6.20+** - Client-side routing
- **React Query 5.8+** - Server state management
- **Axios 1.6+** - HTTP client
- **Recharts 2.12+** - Data visualization

### Database
- **SQL Server 2019+** - Primary database
- **ODBC Driver 18** - Database connectivity

Remember: This system manages **real construction project workflows** with **financial and scheduling implications**. Always verify database operations and maintain data integrity.</content>
<parameter name="filePath">c:\Users\RicoStrinati\Documents\research\BIMProjMngmt\.github\copilot-instructions.md