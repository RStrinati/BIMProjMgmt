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
1. **Project Setup** → **Bid/Contract Management** → **Review Cycles** → **Task Assignment** → **Billing Claims**
2. **Issue Tracking** → **Issue Anchor Linking** → **Analytics & Dashboards**
3. **External Data Imports**: ACC ZIP files, APS OAuth API, Revit health checks, IFC models, Revizto extractions
4. **Review Management**: Multi-stage construction reviews with scheduling, deliverables, and service billing
5. **Data Warehouse**: Incremental ETL pipeline with SCD2 dimensions, fact tables, and mart views

## 🚫 CRITICAL: Items vs Tasks (DO NOT VIOLATE)

This section defines non-negotiable architectural rules that prevent ambiguity and regression.

### Core Model (Option A) - AUTHORITATIVE

The system uses this hierarchy:
```
Project → Services → {Reviews, Items}
Project → Tasks
```

### Explicit Rules (NO EXCEPTIONS)

1. **Items are Service-Owned Deliverables**
   - Items belong to Services (foreign key: `service_id`)
   - Items represent offerings, scopes, or deliverables
   - Examples: "Weekly progress report", "RFI submittal review set"
   - Items are NOT execution tasks

2. **Tasks are Project-Owned Execution Units**
   - Tasks belong to Projects (foreign key: `project_id`)
   - Tasks represent work to be done or tracked
   - Examples: "Coordinate HVAC ductwork", "Prepare submittal response"
   - Tasks are independent of Services, Reviews, and Items
   - A task MAY reference a service for context, but is not "owned by" that service

3. **Reviews and Items are Independent Peers Under Services**
   - Both attach directly to Services (both require `service_id`)
   - Reviews are recurring cycles/meetings (cadence-based)
   - Items are one-off or bundled deliverables
   - There is NO foreign key from Items → Reviews
   - There is NO foreign key from Reviews → Items
   - A Review does NOT require Items to exist
   - Items do NOT require Review cycles to exist

4. **Never Model Items as Tasks**
   - ❌ DO NOT create a Task for a Service Item
   - ❌ DO NOT add `task_id` foreign key to Items table
   - ❌ DO NOT move Items into the Tasks system
   - ✅ DO model Item delivery/status independently in Items table

5. **Never Force Import Data into Tasks**
   - ❌ DO NOT create a Task entry for unmapped ACC issues
   - ❌ DO NOT require an Item to belong to a Review
   - ✅ DO attach imports to Project and Service with optional Review/Item context
   - ✅ DO preserve unmapped state for later manual assignment

6. **Mandatory Foreign Keys (Enforce in Schema)**
   - `Items.service_id` (required, FK to Services)
   - `Reviews.service_id` (required, FK to Services)
   - `Tasks.project_id` (required, FK to Projects)
   - NO Items.review_id foreign key
   - NO Reviews.item_id foreign key
   - NO Items.task_id foreign key

### Core Model Invariants (MUST PRESERVE)

These invariants are non-negotiable and must be enforced in all code:

| Invariant | Rule | Violation |
|-----------|------|-----------|
| **Service Scope** | Every Item requires a Service | Item without service_id is a bug |
| **Review Scope** | Every Review requires a Service | Review without service_id is a bug |
| **Task Scope** | Every Task requires a Project | Task without project_id is a bug |
| **Review Independence** | Reviews do NOT require Items | A service can have reviews with no items |
| **Item Independence** | Items do NOT require Reviews | A service can have items with no reviews |
| **Task Independence** | Tasks do NOT belong to Services | A task cannot have a service_id |
| **Import Flexibility** | Data imports MAY be unmapped | Unmapped imports are valid state, not errors |

### Import Linking Priority (AUTHORITATIVE ORDER)

When linking external data (ACC issues, Revizto, health checks), use this priority:

```
1. project_id (ALWAYS REQUIRED)
   ↓
2. service_id (PRIMARY - use when scope is clear)
   ↓
3. review_id (OPTIONAL - context only)
   ↓
4. item_id (OPTIONAL - context only)
   ↓
5. UNMAPPED (VALID STATE - when mapping is undefined)
```

**Example Import Linking:**
```
ACC Issue from "Design Review" project:
├─ project_id = 123 (always)
├─ service_id = 45 (design review service)
├─ review_id = 789 (optional: specific review cycle)
├─ item_id = null (optional: not linked to any deliverable)
└─ Status: Valid and complete

Revizto issue without clear service mapping:
├─ project_id = 123 (always)
├─ service_id = null (mapping not yet determined)
├─ review_id = null (cannot infer without service)
├─ item_id = null (cannot infer without service)
└─ Status: UNMAPPED but valid - awaiting manual scoping
```

### Code Examples (CORRECT vs INCORRECT)

**❌ INCORRECT - Items modeled as Tasks**
```python
# BAD: Do NOT do this
item = create_task(
    project_id=123,
    name="Weekly Progress Report",
    status="pending"
)
# This conflates Items (service deliverables) with Tasks (execution)
```

**✅ CORRECT - Items modeled independently**
```python
# GOOD: Use the Item system
item = create_service_item(
    service_id=45,  # Item always requires service
    name="Weekly Progress Report",
    item_type="report",
    status="pending"
)

# Separately, a Task for execution:
task = create_project_task(
    project_id=123,  # Task always requires project
    name="Prepare this week's progress report",
    item_id=item.id  # Optional context link
)
```

**❌ INCORRECT - Forcing imports into Tasks**
```python
# BAD: Do NOT do this
def import_acc_issues(project_id, issues):
    for issue in issues:
        create_task(project_id, issue.title)  # Wrong!
        # This loses the fact that these are ACC issues, not project tasks
```

**✅ CORRECT - Linking imports with priority**
```python
# GOOD: Use import priority
def import_acc_issues(project_id, service_id=None, review_id=None, issues=[]):
    for issue in issues:
        link = {
            "project_id": project_id,  # Always
            "service_id": service_id,   # If known
            "review_id": review_id,     # If specific cycle
            "issue_source": "ACC",
            "status": "imported"
        }
        create_issue_link(link)
        # Preserves import fidelity; unmapped issues are visible
```

---

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
# Use connection pooling and schema constants, never hardcode table/column names
from database_pool import get_db_connection
from constants import schema as S

conn = get_db_connection()
try:
    cursor = conn.cursor()
    # Always use schema constants
    cursor.execute(f"SELECT {S.Projects.ID}, {S.Projects.NAME} FROM {S.Projects.TABLE}")
    results = cursor.fetchall()
    conn.commit()
finally:
    conn.close()  # Returns connection to pool, not a true close
```

## Project-Specific Conventions

### File Organization Rules
- **Tests**: All test files MUST be placed in the `tests/` directory
- **Tools**: All analysis, debugging, and utility scripts MUST be placed in the `tools/` directory  
- **Services**: Business logic services MUST be placed in the `services/` directory
- **UI Components**: Individual UI components MUST be placed in the `ui/` directory
- **Handlers**: Data import/export handlers MUST be placed in the `handlers/` directory
- **Constants**: Schema and configuration constants MUST be placed in the `constants/` directory
- **Documentation**: All `.md` documentation files MUST be placed in the `docs/` directory with appropriate subdirectories:
  - `docs/core/` - Core system documentation
  - `docs/features/` - Feature-specific guides
  - `docs/integrations/` - Integration guides (ACC, APS, Revizto, etc.)
  - `docs/reference/` - API references and technical specifications
  - `docs/troubleshooting/` - Troubleshooting guides
  - `docs/migration/` - Database migration and upgrade guides
  - `docs/archive/` - Historical and deprecated documentation
  - Root level `README.md` and project-level `AGENTS.md` are exceptions
- **Database Scripts**: All `.sql` scripts MUST be placed in the `sql/` directory with appropriate subdirectories:
  - `sql/tables/` - Table creation and modification scripts
  - `sql/views/` - View definitions
  - `sql/migrations/` - Schema migration and patch scripts
  - `sql/stored_procedures/` - Stored procedure definitions
  - Do NOT place `.sql` files in `backend/` or other subdirectories
- **Import Paths**: Files in subdirectories MUST use proper parent directory imports:
  ```python
  # For files in tests/, tools/, services/, etc.
  import sys
  import os
  sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
  ```

**CRITICAL**: A clean and organised file system is imperative to this tool. Never place test files, analysis scripts, utilities, SQL scripts, or documentation in the root directory. Only keep:
- `README.md` (project overview)
- `AGENTS.md` (agent workflow settings)
- `config.py`, `database.py`, `database_pool.py` (core application files)
- `requirements.txt`, `pytest.ini` (configuration)
- Top-level source files like `review_management_service.py` (core business logic)

### Schema Constants Pattern
- **Always** import from `constants/schema.py` for table/column references
- **Never** use string literals for database identifiers
- Example: `S.Projects.TABLE`, `S.ReviewSchedule.ASSIGNED_TO`

### Database Connection Management
```python
# IMPORTANT: Use connection_pool.py for ALL database operations
# Connection pooling is 100% migrated as of October 2025
from database_pool import get_db_connection

# Always use context managers or explicit close()
conn = get_db_connection()
try:
    cursor = conn.cursor()
    # ... operations ...
    conn.commit()
finally:
    conn.close()  # Returns to pool, not a true close()
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
- Review cycles link directly to service billing and billing claims

### Bid & Contract Management (NEW)
- Bids have a complete lifecycle: creation → scoping → award → archive
- Scope items can be imported from templates
- Program stages define project timeline
- Billing schedule tracks monetary milestones
- Variations track scope changes and amendments
- Each bid integrates with project financials and reviews

### Issue Anchor Linking (NEW)
- Issues can be linked to project anchors (buildings, areas, phases, etc.)
- Multiple anchor types supported per project configuration
- Anchor links enable issue filtering and visualization by location
- Used for coordination and location-based issue distribution

### Data Warehouse Pipeline (NEW)
- Incremental ETL in `warehouse/etl/pipeline.py` orchestrates all loads
- Uses watermark-based incremental extraction
- Implements SCD2 (Slowly Changing Dimensions) for dimensional tables
- Daily fact loads for issue snapshots and trends
- Data quality checks run after every load
- Query execution times logged to `logs/warehouse.log`

### Issue Categorization & Reliability
- ML-powered issue classification using NLP (`issue_categorizer.py`)
- Issue reliability report tracks source system confidence
- Status/priority/discipline normalization across ACC and Revizto
- Anchor linking enhances issue location accuracy

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

**Playwright Coverage (Initial Scope - Q1 2026):**
- ✅ Project creation and initialization
- ✅ Service application from templates
- ✅ Review cycle creation
- ✅ Service Item creation and management
- ✅ Import run summaries and logs
- ⏳ Dashboards (deferred - analytics layer rewrite in progress)
- ⏳ Billing and claims (deferred - awaiting UI finalization)
- ⏳ Bid management (deferred - awaiting bid workflow UI)

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
- `acc_handler.py` - ACC ZIP file processing and issue ingestion
- `rvt_health_importer.py` - Revit health check Excel import
- `ideate_health_exporter.py` - Health data export for Ideate
- `process_ifc.py` - IFC model geometry extraction

### Business Logic Services
- `issue_categorizer.py` - ML-powered issue classification (NLP)
- `issue_analytics_service.py` - Issue trend and pattern analysis
- `naming_convention_service.py` - Naming compliance validation
- `revit_naming_validator_service.py` - Revit-specific naming checks
- `project_alias_service.py` - Project mapping and alias logic
- `dynamo_batch_service.py` - Dynamo script batch execution
- `review_service.py` - Review cycle and service review operations
- `revit_health_warehouse_service.py` - Health data warehouse integration

### Data Warehouse ETL
- `warehouse/etl/pipeline.py` - Main ETL orchestration engine
- Staging tables for incremental extraction
- Dimension tables with SCD2 change tracking
- Fact tables for issue snapshots and service metrics
- Mart views for analytics and reporting

### Utility Scripts
- `check_schema.py` - Schema validation and auto-fix
- `verify_schema.py` - Schema verification
- `tools/db/check_database_state.py` - Database connection testing

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

## Latest Features & Capabilities (January 2026)

### New Bid & Contract Management Module
- Complete bid lifecycle management with creation, scoping, award, and archive states
- Scope item templates for quick bid creation
- Program stage planning and scheduling
- Billing schedule with line-item detail and milestone tracking
- Variation management for scope changes and amendments
- Award processing with historical tracking
- Integration with project financials and service billing

### Issue Anchor Linking System
- Link construction issues to specific project anchors (buildings, areas, phases, levels, etc.)
- Multiple anchor type support configurable per project
- Anchor-based issue filtering and visualization in analytics
- Project hierarchy navigation with anchor context
- Anchor-to-issue mappings stored in `IssueAnchorLinks` table
- Enables location-based issue distribution and coordination

### Enhanced Issue Analytics
- Issue reliability report showing data quality by source system
- ML-powered issue categorization using NLP (NLTK + sentence-transformers)
- Issue anchor linking for location-based analysis
- Automated status/priority/discipline normalization
- Issue trend analysis with monthly snapshots
- Source system confidence scoring for data quality assessment

### Data Warehouse & Analytics
- Incremental ETL pipeline in `warehouse/etl/pipeline.py` (100% operational)
- SCD2 dimension tables for slowly changing project/service attributes
- Daily issue snapshot facts with age/resolution metrics
- Monthly service metrics aggregation
- Data quality validation checks after every load
- Mart views for analytics and reporting
- Query performance logging to `logs/warehouse.log`

### Building Envelope Performance (BEP) Matrix
- Configurable BEP sections with versioning and defaults
- Section approval workflows with user sign-offs
- BEP content management and template system
- Project-level approval tracking

Remember: This system manages **real construction project workflows** with **financial and scheduling implications**. Always verify database operations and maintain data integrity.</content>
<parameter name="filePath">c:\Users\RicoStrinati\Documents\research\BIMProjMngmt\.github\copilot-instructions.md