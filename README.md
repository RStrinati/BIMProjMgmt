# BIM Project Management System

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![SQL Server](https://img.shields.io/badge/database-SQL%20Server-red.svg)](https://www.microsoft.com/en-us/sql-server)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A comprehensive **BIM (Building Information Modeling) project management system** with integrated review management, scheduling, billing workflows, and analytics capabilities.

## 🎯 Overview

This system manages construction project reviews, scheduling, billing workflows, and data integration from multiple sources including Autodesk Construction Cloud (ACC) and Revit health checks. It provides a complete project lifecycle management solution with:

- **Project Setup & Configuration** - Complete project initialization with templates
- **Review Management** - Multi-stage construction reviews with scheduling and deliverables
- **Task Management** - Enhanced task tracking with dependencies and progress monitoring
- **Issue Analytics** - Advanced analytics dashboard for ACC issues with categorization
- **Resource Management** - Team allocation and capacity planning
- **Billing & Claims** - Automated billing claim generation based on progress
- **Data Integration** - ACC ZIP imports, Revit health checks, IFC model processing

## 🏗️ Architecture

### Core Components

- **Web UI**: React + TypeScript app in `frontend/` (Vite + MUI)
- **Backend**: Flask API (`backend/app.py`) serving REST endpoints for the web client
- **Database**: SQL Server with 3 integrated databases:
  - `ProjectManagement` - Main project/review data
  - `acc_data_schema` - Autodesk Construction Cloud imports
  - `RevitHealthCheckDB` - Revit model health data
- **Data Access**: Centralized database layer (`database.py`) with pyodbc
- **Configuration**: Environment-based config (`config.py`)

### Key Data Flows

```
Project Setup → Review Cycles → Task Assignment → Progress Tracking → Billing Claims
     ↓              ↓                ↓                   ↓                ↓
External Data: ACC ZIP files, Revit health checks, IFC models → Analytics Dashboard
```
The legacy Tkinter desktop UI has been retired in favor of the web experience; archived references now live in `docs/archive/desktop-ui`.

## ⚠️ Important: Codebase Cleanup Required

**This codebase requires organization cleanup before active development.** See:
- 📋 **[CLEANUP_SUMMARY.md](./docs/cleanup/CLEANUP_SUMMARY.md)** - Executive summary of cleanup needed
- 🚀 **[CLEANUP_QUICKSTART.md](./docs/cleanup/CLEANUP_QUICKSTART.md)** - Start cleanup immediately (10 min)
- 📊 **[CLEANUP_REPORT.md](./docs/cleanup/CLEANUP_REPORT.md)** - Complete analysis and action plan
- 📁 **[FILE_ORGANIZATION_GUIDE.md](./docs/cleanup/FILE_ORGANIZATION_GUIDE.md)** - Organization rules for developers

**Quick cleanup:** Run `.\scripts\cleanup_phase1.ps1 -DryRun` to see what will be fixed.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- SQL Server (2019+)
- ODBC Driver 18 for SQL Server
- Access to project databases

### Environment Variables

Set the following environment variables (or create a `.env` file):

```bash
# Database Connection
DB_SERVER=your-server-name
DB_USER=your-username
DB_PASSWORD=your-password
DB_DRIVER={ODBC Driver 18 for SQL Server}

# Database Names
PROJECT_MGMT_DB=ProjectManagement
ACC_DB=acc_data_schema
REVIT_HEALTH_DB=RevitHealthCheckDB
```

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/RStrinati/BIMProjMgmt.git
   cd BIMProjMngmt
   ```

2. **Set up virtual environment**
   ```bash
   # On Windows (PowerShell)
   ./setup_env.sh
   
   # Or manually
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Initialize database schema**
   ```bash
   python scripts/check_schema.py --autofix --update-constants
   ```

4. **Launch the backend API**
   ```bash
   python backend/app.py
   ```

5. **Launch the web UI**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## 📚 Application Modules
These modules surface through the web dashboard:

### 1. Project Setup
- Create and configure new projects
- Apply service templates (SINSW-MPHS, AWS-Day1, NEXTDC-S5)
- Manage project bookmarks and quick access
- Configure project aliases for external system integration

### 2. Enhanced Task Management
- Task creation with dependencies and priorities
- Progress tracking and status workflows
- Milestone management with Gantt visualization
- Resource allocation and effort estimation

### 3. Resource Management
- Team member capacity planning
- Skills and role level tracking
- Workload visualization across projects
- Hourly rate and cost management

### 4. Issue Management (Analytics Dashboard)
- Import ACC issues from ZIP exports
- Automated issue categorization using keywords
- Multi-dimensional analytics (by type, priority, status, discipline)
- Interactive visualizations and filtering
- Export capabilities for reporting

### 5. Review Management
- Multi-stage review workflows (Design, Construction, etc.)
- Review cycle generation with configurable cadence
- Deliverable tracking per review
- Status management and scheduling
- Integration with billing claims

### 6. Document Management
- Document tracking and versioning
- Review deliverable management
- File organization by review cycle
- Status tracking and approvals

### 7. Project Bookmarks
- Quick access to frequently used projects
- Custom bookmark organization
- Project switching and navigation

### 8. Project Alias Management
- External system integration mappings
- ACC project linking
- Cross-reference management

## 🔧 Advanced Features

### Database Schema Management
```bash
# Validate schema compatibility
   python scripts/check_schema.py

# Auto-fix schema issues
   python scripts/check_schema.py --autofix

# Update schema constants
   python scripts/check_schema.py --update-constants
```

### Data Import Operations

#### ACC Issues Import
```python
from handlers.acc_handler import import_acc_zip
import_acc_zip('path/to/acc_export.zip', project_id=123)
```

#### Revit Health Check Import
```python
from handlers.rvt_health_importer import import_revit_health
import_revit_health('path/to/health_export.xlsx')
```

#### IFC Model Processing
```python
from handlers.process_ifc import process_ifc_file
process_ifc_file('path/to/model.ifc')
```

### API Endpoints

The Flask backend provides RESTful APIs:

- `GET /api/projects` - List all projects
- `GET /api/projects/<id>` - Get project details
- `PUT /api/projects/<id>` - Update project
- `GET /api/reviews/<project_id>` - Get project reviews
- `POST /api/reviews` - Create new review
- `GET /api/tasks/<project_id>` - Get project tasks
- `POST /api/billing/claims` - Generate billing claim

## 📊 Database Schema

The system uses a normalized SQL Server schema with the following core tables:

### Project Management
- `Projects` - Project master data
- `ProjectServices` - Service definitions and pricing
- `ServiceTemplates` - Reusable service templates
- `ReviewSchedule` - Review cycle scheduling
- `ReviewParameters` - Review configuration and deliverables

### Task & Resource Management
- `Tasks` - Task tracking with dependencies
- `Milestones` - Project milestones and targets
- `Users` - Team members and resource data

### Billing & Claims
- `BillingClaims` - Monthly billing claims
- `BillingClaimLines` - Claim line items with progress tracking

### External Integrations
- `AccImportFolders` - ACC data import tracking
- `AccImportLogs` - Import history and status
- `tblACCDocs` - ACC document metadata

See [docs/database_schema.md](docs/database_schema.md) for complete schema documentation.

## 🧪 Testing

Run the comprehensive test suite:

```bash
# All tests
python -m pytest tests/

# Specific test categories
python -m pytest tests/test_review_management.py
python -m pytest tests/test_analytics_dashboard.py
python -m pytest tests/test_project_services.py

# With coverage
python -m pytest --cov=. tests/
```

## 📁 Project Structure

```
BIMProjMngmt/
??? backend/                    # Flask API
??? frontend/                   # React web UI (Vite)
??? database.py                 # Database access layer
??? review_management_service.py # Review business logic
??? config.py                   # Configuration management
??? requirements.txt            # Python dependencies

??? handlers/                   # Data import handlers (ACC, Revit)
?   ??? acc_handler.py
?   ??? rvt_health_importer.py
?   ??? process_ifc.py

??? services/                   # Runtime services (incl. revizto-dotnet)
??? constants/                  # Schema constants
?   ??? schema.py

??? sql/                        # Database scripts
?   ??? tables/                 # Table creation scripts
?   ??? views/                  # View definitions
?   ??? migrations/             # Schema migrations

??? templates/                  # Service templates (JSON)
??? tests/                      # Test suite
??? scripts/                    # Entrypoint/ops scripts
??? tools/                      # Maintenance utilities (db/, imports/, analytics/, docs/)
??? docs/                       # Documentation
```

## 🔐 Security & Best Practices

### Schema Constants Pattern
Always use schema constants instead of hardcoded strings:

```python
from constants import schema as S

# ✅ Good
cursor.execute(f"SELECT {S.Projects.ID}, {S.Projects.NAME} FROM {S.Projects.TABLE}")

# ❌ Bad
cursor.execute("SELECT project_id, project_name FROM projects")
```

### Database Connection Management
Always use context managers or explicit cleanup:

```python
from database import connect_to_db

conn = connect_to_db()
try:
    cursor = conn.cursor()
    # ... operations ...
    conn.commit()
finally:
    conn.close()
```

## 🗺️ Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for the detailed development roadmap.

### Completed Features ✅
- ✅ Core project and review management
- ✅ Enhanced task management with dependencies
- ✅ Issue analytics dashboard with categorization
- ✅ Service templates and billing claims
- ✅ Project alias management
- ✅ ACC data integration
- ✅ Revit health check imports

### In Progress 🚧
- 🚧 Advanced reporting and dashboards
- 🚧 Real-time collaboration features
- 🚧 Mobile application companion

### Planned Features 📋
- 📋 AI-powered issue categorization
- 📋 Automated risk detection
- 📋 Integration with additional BIM platforms
- 📋 Advanced financial forecasting

## 📖 Documentation

### Core Documentation
- [Database Schema](docs/database_schema.md) - Complete schema reference
- [Implementation Guide](docs/IMPLEMENTATION_COMPLETE.md) - Implementation details
- [Issue Analytics Guide](docs/ISSUE_ANALYTICS_QUICKSTART.md) - Analytics dashboard usage
- [Review Management](docs/enhanced_review_management_overview.md) - Review workflow guide
- [Roadmap](docs/ROADMAP.md) - Development roadmap and future features

### Developer Guides (NEW)
- **[Database Connection Guide](docs/DATABASE_CONNECTION_GUIDE.md)** ⭐ - **MANDATORY** database patterns for all developers
  - Connection pool usage (100% migrated as of October 2025)
  - Code examples and best practices
  - Migration patterns and troubleshooting
  - Performance optimization guidelines
  
- **[React Integration Roadmap](docs/REACT_INTEGRATION_ROADMAP.md)** - Complete frontend development plan
  - Phase-by-phase implementation guide (4-6 months)
  - Technology stack recommendations
  - API enhancement requirements
  - Testing and deployment strategy
  
### Migration Reports
- [DB Migration Phase 4 Complete](docs/DB_MIGRATION_PHASE4_COMPLETE.md) - Latest migration (October 2025)
- [DB Migration Session 3](docs/DB_MIGRATION_SESSION3_COMPLETE.md) - Previous migration session
- [Database Migration Complete](docs/DATABASE_MIGRATION_COMPLETE.md) - Overall migration summary

## 🤝 Contributing

This is a private project for construction project management. For questions or issues, please contact the repository owner.

## 📄 License

Copyright © 2025 Rico Strinati. All rights reserved.

## 🆘 Support

For issues, questions, or feature requests:
1. Check existing documentation in `/docs`
2. Review test files in `/tests` for usage examples
3. Contact the development team

---

**Note**: This system manages real construction project workflows with financial and scheduling implications. Always verify database operations and maintain data integrity.
