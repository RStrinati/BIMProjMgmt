# BIM Project Management System

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![React 18.2+](https://img.shields.io/badge/react-18.2+-61DAFB.svg)](https://reactjs.org/)
[![TypeScript 5.2+](https://img.shields.io/badge/typescript-5.2+-3178C6.svg)](https://www.typescriptlang.org/)
[![SQL Server](https://img.shields.io/badge/database-SQL%20Server-red.svg)](https://www.microsoft.com/en-us/sql-server)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A comprehensive **BIM (Building Information Modeling) project management system** with integrated review management, scheduling, billing workflows, real-time analytics, and multi-platform data integration capabilities.

## 🎯 Overview

This system provides enterprise-grade construction project lifecycle management with real-time collaboration, multi-source data integration, and advanced analytics. Built with modern web technologies, it integrates seamlessly with Autodesk Construction Cloud (ACC), Revizto, and Revit workflows.

### Core Capabilities

- **🏗️ Project Lifecycle Management** - Complete project initialization, tracking, and closeout with service templates
- **📋 Review Management** - Multi-stage construction reviews with automated scheduling and deliverables tracking
- **✅ Task Management** - Enhanced task tracking with dependencies, milestones, and Gantt visualization
- **📊 Real-Time Analytics** - Interactive dashboards for issues, model health, naming compliance, and coordinate alignment
- **👥 Resource Management** - Team allocation, capacity planning, and workload visualization
- **💰 Billing & Claims** - Automated billing claim generation with progress tracking and line-item detail
- **🔗 Data Integration** - ACC, Revizto, Revit Health, IFC models, and Autodesk Platform Services (APS)
- **🤖 Automation** - Dynamo batch processing, automated health checks, and issue pattern recognition

## 📐 Core Conceptual Model (AUTHORITATIVE - Option A)

The entire system is organized around this data model hierarchy:

```
Project
├─ Services (project offerings/scopes)
│  ├─ Reviews (recurring cycles/meetings - cadence-based)
│  └─ Items (service deliverables - one-off or bundled)
└─ Tasks (project-owned execution units - independent)
```

### Key Definitions

| Concept | Definition | Scope | Examples |
|---------|-----------|-------|----------|
| **Project** | Container for all project work, scheduling, and resources | Everything in this system | Construction project, renovation, consulting engagement |
| **Service** (ProjectService) | A defined offering/scope of work sold to the client | Under a project | Design review, construction admin, quality assurance |
| **Review** (ServiceReview) | Recurring meeting/cycle for a service at regular cadence | Under a service | Weekly design review, bi-weekly progress review |
| **Item** (ServiceItem) | A specific deliverable or offering within a service | Under a service | Monthly inspection report, submittal review set, schedule update |
| **Task** (ProjectTask) | Execution unit for work, tracked independently across project | Under a project (not under service/review/item) | Complete model review, prepare RFI response, schedule coordination meeting |

### Critical Relationships & Rules

- **Items are NOT Tasks**: Items are service-owned deliverables. Tasks are project-owned execution units.
- **Reviews and Items are peers**: Both attach directly to Services independently. Neither requires the other.
- **Service Independence**: Reviews and Items operate independently—a Review cycle does not require Items, and Items do not require Review cycles.
- **No mandatory cross-references**: There is no `review_id` foreign key in Items, and no `item_id` foreign key in Reviews.
- **Task Independence**: Tasks are scoped to the project, not to individual Services, Reviews, or Items (though they may reference these for context).
- **Unmapped imports are valid**: External data (ACC issues, Revizto extractions) can attach to Project or Service without requiring Review or Item mapping.

### What This Means in Practice

```python
# Service lifecycle
service = Project.add_service(name="Construction Administration")

# Option 1: Set up recurring reviews (cadence-based)
reviews = service.add_review_cycles(cadence="weekly", stage="construction")

# Option 2: Define deliverables/items (service offerings)
items = service.add_items([
  {"name": "Weekly Progress Report", "type": "report"},
  {"name": "RFI Submittal Review", "type": "review"}
])

# Option 3: Both—independent of each other
# Weekly reviews happen at a cadence; items are delivered per scope

# Separate from all of the above: project-level execution
task = Project.add_task(name="Coordinate HVAC ductwork", priority="high")
# This task can reference the Construction Admin service for context,
# but it is not "owned by" or "under" that service
```

---

## 🏗️ Architecture

### Technology Stack

#### Frontend (React Web Application)
- **React 18.2+** - Modern UI library with hooks and concurrent features
- **TypeScript 5.2+** - Type-safe development with enhanced IDE support
- **Vite 5.0** - Lightning-fast dev server and optimized production builds
- **Material-UI 5.14+** - Professional component library with theming
- **React Router 6.20+** - Client-side routing and navigation
- **React Query 5.8+** (TanStack Query) - Server state management with caching
- **Axios 1.6+** - HTTP client with request/response interceptors
- **Recharts 2.12+** - Data visualization and interactive charts
- **date-fns 2.30** - Modern date manipulation and formatting

#### Backend (Python Flask API)
- **Flask** - RESTful API framework with request routing
- **Flask-CORS** - Cross-origin resource sharing for web client
- **pyodbc** - SQL Server database connectivity via ODBC
- **pandas** - Data analysis and manipulation
- **ifcopenshell** - IFC model processing and geometry extraction
- **nltk 3.8+** - Natural language processing for issue categorization
- **scikit-learn 1.3+** - Machine learning for pattern recognition
- **sentence-transformers 2.2+** - Semantic similarity for issue clustering

#### Database Layer
- **SQL Server 2019+** - Primary relational database
- **ODBC Driver 18** - High-performance database connectivity
- **Connection Pooling** - Optimized connection management (100% migrated Oct 2025)
- **3 Integrated Databases:**
  - `ProjectManagement` - Core project/review/billing data
  - `acc_data_schema` - Autodesk Construction Cloud imports
  - `RevitHealthCheckDB` - Revit model health metrics

#### External Services Integration
- **Autodesk Platform Services (APS)** - OAuth authentication and data API
- **Autodesk Construction Cloud (ACC)** - Issues, documents, and project data
- **Revizto API** - Issue extraction and model coordination
- **.NET Services** - Revizto data extraction service (C# microservice)

### Core Components

- **Web UI**: React + TypeScript SPA in `frontend/` (port 5173 in dev)
- **Backend API**: Flask REST server in `backend/app.py` (port 5000)
- **Database Layer**: Centralized in `database.py` with connection pooling via `database_pool.py`
- **Business Logic**: Service modules in `services/` and `review_management_service.py`
- **Data Handlers**: Import/export handlers in `handlers/` (ACC, Revit, IFC)
- **Analytics Engine**: Warehouse queries and dashboard metrics in `warehouse/`
- **Configuration**: Environment-based config in `config.py`

### Key Data Flows

```
User (Browser) → React Frontend → Axios API Client → Flask Backend → pyodbc → SQL Server
                      ↓                                      ↓
                React Query Cache              Connection Pool (database_pool.py)
                      ↓                                      ↓
              UI Components                    Business Logic Services
                                                             ↓
External Data Sources:                         Database Operations & Queries
  - ACC ZIP Exports                                        ↓
  - APS REST API                              Analytics & Reporting (warehouse/)
  - Revizto Issues
  - Revit Health Excel
  - IFC Models                               
```

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

## 📚 Application Features & Modules

Access all features through the modern web dashboard at `http://localhost:5173` (development) or your deployed URL.

### Navigation & Workspace
- **Project Workspace**: Dedicated workspace per project with all services, reviews, and tasks
- **Multi-Panel UI**: Side-by-side navigation with detail panels (Projects, Bids, Analytics)
- **Breadcrumb Navigation**: Context-aware navigation across hierarchies
- **Workspace Persistence**: Save and restore workspace state per user

### 1. Project Management Dashboard
- **Project Creation & Configuration** - Initialize new projects with comprehensive metadata
- **Service Templates** - Apply pre-configured templates (SINSW-MPHS, AWS-Day1, NEXTDC-S5)
- **Project Statistics** - Real-time metrics, active reviews, task counts, resource allocation
- **Project Bookmarks** - Quick access favorites with custom organization
- **Client Management** - Client database with contact information and project associations
- **Project Types** - Customizable project type definitions for categorization

### 2. Review Management System
- **Multi-Stage Workflows** - Design reviews, construction reviews, quality assurance
- **Automated Cycle Generation** - Configurable cadence (weekly, biweekly, monthly)
- **Deliverable Tracking** - Document management per review cycle with status tracking
- **Review Scheduling** - Planned vs actual dates with progress monitoring
- **Billing Integration** - Direct link to billing claims with completion percentages
- **Status Management** - Review lifecycle tracking (scheduled, in-progress, completed)

### 3. Advanced Task Management
- **Task Dependencies** - Predecessor/successor relationships with Gantt visualization
- **Milestone Tracking** - Project milestones with target dates and progress
- **Priority Levels** - Critical, high, medium, low priority classification
- **Assignment & Allocation** - User assignment with effort estimation
- **Progress Monitoring** - Percentage complete with status workflows
- **Notes & Checklists** - Task items with completion toggle and detailed notes

### 4. Resource & Team Management
- **User Administration** - Team member profiles with roles and contact info
- **Capacity Planning** - Workload visualization across all projects
- **Skills Matrix** - Technical skills and role level tracking
- **Hourly Rate Management** - Cost tracking and billing rate configuration
- **Assignment Reassignment** - Bulk reassignment of reviews and services
- **Workload Analytics** - Current assignments and availability dashboard

### 5. Issue Analytics Dashboard
- **Multi-Source Integration** - ACC issues, Revizto issues, custom issue tracking with unified interface
- **Automated Categorization** - ML-powered issue classification using NLP and semantic analysis
- **Advanced Filtering** - By project, type, priority, status, discipline, date range, anchor location
- **Issue Anchor Linking** - Link issues to specific project anchors (buildings, areas, phases)
- **Interactive Visualizations**:
  - Issue trends over time (line charts with date range selection)
  - Distribution by type, priority, status (pie/bar charts)
  - Discipline-specific breakdowns
  - Age analysis and resolution metrics
  - Anchor-based issue distribution
- **Issue Overview** - Cross-project and per-project summaries with KPIs and trend analysis
- **Issue Reliability Metrics** - Track issue data quality and source system confidence
- **Export Capabilities** - CSV/Excel export for external reporting
- **Issue Detail Views** - Comprehensive issue records with linked anchors and metadata

### 6. Model Health & Quality Dashboards
- **Revit Health Monitoring**:
  - Overall health scores and file metrics
  - Warning and error tracking
  - Family performance analysis
  - View complexity metrics
  - File size and element count tracking
- **Naming Compliance**:
  - Convention validation against project standards
  - Non-compliant element identification
  - Automated revalidation triggers
  - Compliance percentage by category
- **Grid & Level Alignment**:
  - Cross-model coordinate validation
  - Grid naming consistency checks
  - Level elevation alignment
  - Tolerance-based mismatch detection
- **Control Points**:
  - Survey control point tracking
  - Coordinate system verification
  - Deviation analysis

### 7. Data Import & Integration
- **ACC Data Import**:
  - ZIP file extraction and processing
  - Document metadata import
  - Issue synchronization
  - Import history and logs
- **APS (Autodesk Platform Services) Integration**:
  - OAuth authentication flow
  - Hub and project browsing
  - Real-time issue sync
  - Folder structure exploration
  - User data retrieval
- **Revizto Integration**:
  - Project mapping and synchronization
  - Issue extraction runs
  - Status monitoring
  - Attribute mapping configuration
- **Revit Health Import**:
  - Excel health check imports
  - Automated metric calculation
  - Historical tracking
  - Health trend analysis
- **IFC Model Processing**:
  - Geometry extraction
  - Metadata parsing
  - Element categorization

#### Import Semantics & Data Attachment

Imported data (issues, health metrics, documents) must be linked to the Core Model in a standardized way:

| Priority | Target | Required? | Use Case | Example |
|----------|--------|-----------|----------|---------|
| 1 (Always) | `Project` | ✅ Yes | All imports attach to a project context | ACC issues always map to a project_id |
| 2 (Primary) | `Service` | ⚠️ Often | Scope-specific imports (design review issues, construction admin deliverables) | Weekly review issues attach to "Design Review" service |
| 3 (Optional) | `Review` | ❌ No | Context only; never required for import validity | An issue *may* reference a specific review cycle for context |
| 4 (Optional) | `Item` | ❌ No | Context only; never required for import validity | An issue *may* reference a deliverable item for context |
| 5 (Valid State) | Unmapped | ✅ Yes | Acceptable when source→target mapping is undefined | ACC project with no local mapping, pending manual assignment |

**Key Principles:**
- Always link to Project (required)
- Prefer Service (recommended when scope is clear)
- Review/Item linkage is optional context only
- Never force unmapped data into artificial Task entries
- Preserve import fidelity—link only what is certain

### 8. Billing & Financial Management
- **Bid & Contract Management**:
  - Comprehensive bid lifecycle (creation, scoping, award, archive)
  - Scope item management with templates
  - Program stage tracking and scheduling
  - Billing schedule with line-item detail
  - Award processing with date tracking
  - Variation tracking for scope changes
- **Billing Claims Generation**:
  - Automated monthly claim creation (from service reviews)
  - Progress-based billing calculation
  - Line item detail with review linkage
- **Service Billing Tracking**:
  - Per-service billing status
  - Review completion percentages
  - Invoicing readiness indicators
- **Financial Reporting**:
  - Revenue by project
  - Billing status dashboards
  - Claim history and trends

### 9. Automation & Batch Processing
- **Dynamo Batch Automation**:
  - Script library management
  - Batch job creation and scheduling
  - Revit file batch processing
  - Execution status monitoring
- **Health Check Automation**:
  - Automated health script execution
  - Scheduled revalidation
  - Batch naming compliance checks
- **Application Launchers**:
  - Revit file opening with version detection
  - Revizto exporter integration
  - External tool coordination

### 10. Project Alias & Mapping
- **External System Integration**:
  - ACC project ID mapping
  - Alias management for cross-reference
  - Auto-mapping suggestions with analysis
  - Validation and verification
  - Project type and configuration mapping
- **Unmapped Project Detection**:
  - Identify unlinked external projects
  - Bulk mapping operations
  - Mapping statistics and coverage
  - Smart alias analysis and validation

### 10a. Building Envelope Performance (BEP) Matrix
- **BEP Section Management**:
  - Configurable BEP sections with versioning
  - Content templates and defaults
  - Section-level approval workflows
- **Approval Tracking**:
  - User approvals with comments
  - Version history and change tracking
  - Project-level approval status

### 10b. Issue Anchor Linking
- **Anchor-Issue Mapping**:
  - Link issues to specific project anchors (areas, buildings, phases)
  - Multiple anchor type support
  - Cross-anchor issue visualization
- **Anchor Navigation**:
  - Project anchor hierarchy navigation
  - Issue filtering by anchor location
  - Anchor-based reporting and analytics

### 11. Document Management
- **Document Tracking** - File versioning and metadata
- **Review Deliverables** - Document association with review cycles
- **File Organization** - Structured storage by project/review
- **Status Tracking** - Approval workflows and document status
- **ACC Document Sync** - Bi-directional synchronization

### 12. Analytics & Reporting Warehouse
- **Data Warehouse Metrics**:
  - Cross-project KPIs
  - Historical trend analysis
  - Performance indicators
- **Custom Dashboards**:
  - Issue history and resolution trends
  - Model register with health metrics
  - Coordinate alignment summary
  - Timeline visualizations
- **Export & Reporting**:
  - CSV/Excel data exports
  - Print-ready report formats
  - Scheduled report generation

## 🔧 Advanced Features & Tools

### Database Schema Management
```bash
# Validate schema compatibility and check for issues
python scripts/check_schema.py

# Auto-fix schema mismatches and update database
python scripts/check_schema.py --autofix

# Update schema constants after manual changes
python scripts/check_schema.py --update-constants

# Verify database state and connections
python tools/db/check_database_state.py
```

### Data Import Operations

#### ACC Issues Import (ZIP Method)
```python
from handlers.acc_handler import import_acc_zip

# Import ACC issues from ZIP export
import_acc_zip('path/to/acc_export.zip', project_id=123)

# Logs stored in backend/logs/acc_import.log
```

#### APS Real-Time Sync (API Method)
```bash
# 1. Get login URL via API
GET /api/aps-sync/login-url

# 2. Browse hubs and projects
GET /api/aps-sync/hubs
GET /api/aps-sync/hubs/{hub_id}/projects

# 3. Sync issues in real-time
GET /api/aps-sync/hubs/{hub_id}/projects/{project_id}/issues

# 4. Retrieve users and folders
GET /api/aps-sync/hubs/{hub_id}/projects/{project_id}/users
GET /api/aps-sync/hubs/{hub_id}/projects/{project_id}/folders
```

#### Revit Health Check Import
```python
from handlers.rvt_health_importer import import_revit_health

# Import health check from Excel export
import_revit_health('path/to/health_export.xlsx', project_id=123)

# Or use API endpoint
POST /api/projects/{project_id}/health-import
Content-Type: multipart/form-data
{
  "file": <health_export.xlsx>
}
```

#### IFC Model Processing
```python
from handlers.process_ifc import process_ifc_file

# Extract geometry and metadata from IFC models
process_ifc_file('path/to/model.ifc')
```

#### Revizto Integration
```python
# Start extraction run via API
POST /api/revizto/start-extraction
{
  "project_uuid": "revizto-project-id",
  "extraction_type": "issues"
}

# Check extraction status
GET /api/revizto/status?run_id=123

# View extraction runs history
GET /api/revizto/extraction-runs

# Requires revizto-dotnet service running (C# microservice)
```

### Automation Tools

#### Dynamo Batch Processing
```bash
# Import Dynamo scripts from folder
POST /api/dynamo/scripts/import-folder
{
  "folder_path": "C:/Dynamo/Scripts",
  "category": "Health Checks"
}

# Create batch job
POST /api/dynamo/jobs
{
  "name": "Monthly Health Check",
  "script_id": 5,
  "revit_files": [101, 102, 103]
}

# Execute batch job
POST /api/dynamo/jobs/{job_id}/execute
```

#### Application Launchers
```bash
# Launch Revit file with version detection
POST /api/applications/launch
{
  "file_path": "C:/Project/Model.rvt"
}

# Run Revizto exporter
POST /api/applications/revizto-exporter
{
  "revit_file_path": "C:/Project/Model.rvt",
  "output_path": "C:/Exports/"
}

# Run health importer script
POST /api/scripts/run-health-importer
{
  "excel_path": "C:/Health/Report.xlsx",
  "project_id": 123
}
```

### Analytics & Reporting

#### Warehouse Dashboard Metrics
```bash
# Get aggregated warehouse metrics
GET /api/dashboard/warehouse-metrics

# Returns:
# - Cross-project statistics
# - Trend analysis
# - Performance indicators
# - Query execution times logged to logs/warehouse.log

# Issue Reliability Report
GET /api/settings/issue-reliability

# Returns:
# - Data quality metrics by source system
# - Issue source confidence scores
# - Mapping accuracy statistics
```

#### Issue Analytics
```bash
# Get issues KPIs
GET /api/dashboard/issues-kpis?project_id=123

# Get issue charts data
GET /api/dashboard/issues-charts?project_id=123&chart_type=trend

# Get paginated issue table
GET /api/dashboard/issues-table?project_id=123&page=1&page_size=50

# Get combined overview
GET /api/issues/overview
GET /api/projects/{project_id}/issues/overview
```

#### Model Health Dashboards
```bash
# Revit health summary
GET /api/dashboard/revit-health?project_id=123

# Naming compliance
GET /api/dashboard/naming-compliance?project_id=123
GET /api/dashboard/naming-compliance/table?project_id=123

# Grid alignment
GET /api/dashboard/health/grids?project_id=123

# Level alignment  
GET /api/dashboard/health/levels?project_id=123

# Control points
GET /api/dashboard/control-points?project_id=123

# Coordinate alignment
GET /api/dashboard/coordinate-alignment?project_id=123

# Model register
GET /api/dashboard/model-register?project_id=123
```

### Configuration Management

#### Environment Variables
```bash
# Database Configuration
DB_SERVER=.\SQLEXPRESS              # SQL Server instance
DB_USER=admin02                     # Database username
DB_PASSWORD=1234                    # Database password
DB_DRIVER={ODBC Driver 18 for SQL Server}

# Database Names
PROJECT_MGMT_DB=ProjectManagement   # Main project database
WAREHOUSE_DB=ProjectManagement      # Analytics warehouse (same as main)
ACC_DB=acc_data_schema              # ACC import database
REVIT_HEALTH_DB=RevitHealthCheckDB  # Revit health database

# External Service URLs (Optional)
ACC_SERVICE_URL=http://localhost:5001        # ACC connector service
ACC_SERVICE_TOKEN=your-token-here
REVIZTO_SERVICE_URL=http://localhost:5002    # Revizto extraction service
REVIZTO_SERVICE_TOKEN=your-token-here
APS_AUTH_SERVICE_URL=http://localhost:5003   # APS auth service
APS_AUTH_LOGIN_PATH=/auth/login
```

#### Service Configuration Files
```bash
# APS auth service configuration
services/aps-auth-demo/appsettings.json

# ACC connector service configuration  
services/acc-node/config/default.json

# Revizto extraction service configuration
services/revizto-dotnet/appsettings.json
```

### API Endpoints Reference

The Flask backend provides comprehensive RESTful APIs. Full documentation available at `http://localhost:5000` when running.

#### Project Management
```
GET    /api/projects                    # List all projects
POST   /api/projects                    # Create new project
GET    /api/projects/{id}               # Get project details
PUT    /api/projects/{id}               # Update project
PATCH  /api/projects/{id}               # Partial update
DELETE /api/projects/{id}               # Delete project
GET    /api/projects_full               # Full project data with relations
GET    /api/projects/stats              # Project statistics
GET    /api/project_details/{id}        # Detailed project info
```

#### Review Management
```
GET    /api/reviews/{project_id}        # Get project reviews
POST   /api/reviews                     # Create review cycle
PUT    /api/reviews/{cycle_id}          # Update review
DELETE /api/reviews/{cycle_id}          # Delete review
GET    /api/review_summary              # Review summary across projects
GET    /api/review_tasks                # All review tasks
GET    /api/review_tasks/{schedule_id}  # Specific review tasks
PUT    /api/review_tasks/{task_id}      # Update review task
```

#### Service Management
```
GET    /api/projects/{id}/services                      # Get project services
POST   /api/projects/{id}/services                      # Create service
POST   /api/projects/{id}/services/apply-template       # Apply service template
PATCH  /api/projects/{id}/services/{service_id}         # Update service
DELETE /api/projects/{id}/services/{service_id}         # Delete service
GET    /api/projects/{id}/services/{service_id}/reviews # Service reviews
GET    /api/projects/{id}/review-billing                # Review billing info
POST   /api/projects/{id}/services/{service_id}/reviews # Create service review
```

#### Task Management
```
GET    /api/tasks                       # Get all tasks (with project_id filter)
POST   /api/tasks                       # Create task
PUT    /api/tasks/{task_id}             # Update task
DELETE /api/tasks/{task_id}             # Delete task
GET    /api/tasks/notes-view            # Tasks with notes view
PUT    /api/tasks/{id}/items/{index}/toggle  # Toggle checklist item
GET    /api/task_dependencies/{task_id} # Get task dependencies
```

#### User & Resource Management
```
GET    /api/users                       # List all users
POST   /api/users                       # Create user
PUT    /api/users/{user_id}             # Update user
DELETE /api/users/{user_id}             # Delete user
PUT    /api/services/{id}/assign        # Assign service to user
PUT    /api/reviews/{id}/assign         # Assign review to user
GET    /api/users/{id}/assignments      # User assignments
POST   /api/users/reassign              # Bulk reassignment
GET    /api/users/workload              # User workload analysis
GET    /api/projects/{id}/lead-user     # Get project lead user
```

#### Analytics Dashboards
```
GET    /api/dashboard/stats                      # Overall dashboard stats
GET    /api/dashboard/warehouse-metrics          # Warehouse aggregated metrics
GET    /api/dashboard/issues-history             # Issue trend history
GET    /api/dashboard/issues-kpis                # Issue KPIs
GET    /api/dashboard/issues-charts              # Issue visualization data
GET    /api/dashboard/issues-table               # Paginated issue table
GET    /api/dashboard/revit-health               # Revit health summary
GET    /api/dashboard/naming-compliance          # Naming compliance metrics
GET    /api/dashboard/naming-compliance/table    # Compliance detail table
GET    /api/dashboard/control-points             # Control points dashboard
GET    /api/dashboard/coordinate-alignment       # Coordinate alignment
GET    /api/dashboard/health/grids               # Grid alignment dashboard
GET    /api/dashboard/health/levels              # Level alignment dashboard
GET    /api/dashboard/model-register             # Model register with health
GET    /api/dashboard/issues-detail              # Detailed issue analysis
GET    /api/dashboard/timeline                   # Project timeline visualization
```

#### Issue Management
```
GET    /api/projects/{id}/acc-issues         # Get ACC issues for project
GET    /api/projects/{id}/acc-issues/stats   # Issue statistics
GET    /api/issues/overview                  # All projects overview
GET    /api/projects/{id}/issues/overview    # Project-specific overview
```

#### Data Import Operations
```
POST   /api/projects/{id}/acc-data-import       # Import ACC ZIP data
GET    /api/projects/{id}/acc-data-import-logs  # ACC import history
POST   /api/projects/{id}/acc-data-folder       # Set ACC data folder
GET    /api/projects/{id}/acc-data-folder       # Get ACC data folder
POST   /api/projects/{id}/health-import         # Import Revit health Excel
GET    /api/projects/{id}/health-files          # Get health files
GET    /api/projects/{id}/health-summary        # Health summary
POST   /api/projects/{id}/revit-health/revalidate-naming  # Revalidate naming
```

#### APS Integration (Autodesk Platform Services)
```
GET    /api/aps-sync/login-url                          # Get OAuth login URL
GET    /api/aps-sync/hubs                               # List accessible hubs
GET    /api/aps-sync/hubs/{hub_id}/projects             # List hub projects
GET    /api/aps-sync/hubs/{hub_id}/projects/{proj_id}/details   # Project details
GET    /api/aps-sync/hubs/{hub_id}/projects/{proj_id}/folders   # Project folders
GET    /api/aps-sync/hubs/{hub_id}/projects/{proj_id}/issues    # Real-time issues
GET    /api/aps-sync/hubs/{hub_id}/projects/{proj_id}/users     # Project users
```

#### Revizto Integration
```
POST   /api/revizto/start-extraction      # Start issue extraction
GET    /api/revizto/status                # Get extraction status
GET    /api/revizto/projects              # List Revizto projects
GET    /api/revizto/extraction-runs       # Extraction history
GET    /api/revizto/extraction-runs/last  # Last extraction run
GET    /api/mappings/revizto-projects     # Get project mappings
POST   /api/mappings/revizto-projects     # Create mapping
DELETE /api/mappings/revizto-projects/{uuid}  # Delete mapping
```

#### Dynamo Automation
```
GET    /api/dynamo/scripts                # List Dynamo scripts
POST   /api/dynamo/scripts/import-folder  # Import scripts from folder
POST   /api/dynamo/scripts/import-files   # Import individual scripts
GET    /api/dynamo/jobs                   # List batch jobs
POST   /api/dynamo/jobs                   # Create batch job
GET    /api/dynamo/jobs/{job_id}          # Get job details
POST   /api/dynamo/jobs/{job_id}/execute  # Execute batch job
```

#### Client & Project Alias Management
```
GET    /api/clients                       # List clients
POST   /api/clients                       # Create client
GET    /api/clients/{id}                  # Get client details
PUT    /api/clients/{id}                  # Update client
DELETE /api/clients/{id}                  # Delete client
GET    /api/project_aliases               # List aliases
POST   /api/project_aliases               # Create alias
PUT    /api/project_aliases/{name}        # Update alias
DELETE /api/project_aliases/{name}        # Delete alias
GET    /api/project_aliases/summary       # Alias statistics
GET    /api/project_aliases/unmapped      # Unmapped projects
POST   /api/project_aliases/auto-map      # Auto-map suggestions
POST   /api/project_aliases/analyze       # Analyze project-alias relationships
GET    /api/project_aliases/validation    # Validation status
```

#### Service Templates
```
GET    /api/service_templates             # List templates
POST   /api/service_templates             # Create template
PATCH  /api/service_templates/{id}        # Update template
DELETE /api/service_templates/{id}        # Delete template
GET    /api/service_templates/file        # Get template file
POST   /api/service_templates/file        # Upload template file
DELETE /api/service_templates/file        # Delete template file
```

#### Bid Management
```
GET    /api/bids                          # List all bids
POST   /api/bids                          # Create new bid
GET    /api/bids/{bid_id}                 # Get bid details
PUT    /api/bids/{bid_id}                 # Update bid
DELETE /api/bids/{bid_id}                 # Delete/archive bid
GET    /api/bids/{bid_id}/scope-items     # Get bid scope items
POST   /api/bids/{bid_id}/scope-items     # Add scope item
PUT    /api/bids/{bid_id}/scope-items/{id}        # Update scope item
DELETE /api/bids/{bid_id}/scope-items/{id}        # Delete scope item
GET    /api/bids/{bid_id}/program-stages  # Get program stages
POST   /api/bids/{bid_id}/program-stages  # Create program stage
GET    /api/bids/{bid_id}/billing-schedule        # Get billing schedule
POST   /api/bids/{bid_id}/billing-schedule        # Add billing line
PUT    /api/bids/{bid_id}/billing-schedule/{id}   # Update billing line
POST   /api/bids/{bid_id}/award           # Award bid (update status)
```

#### Variations & Change Management
```
GET    /api/variations                    # List variations
POST   /api/variations                    # Create variation
```

#### BEP & Approvals
```
GET    /api/bep_matrix                    # Get BEP matrix
GET    /api/reference/{table}             # Get reference options (project_types, etc.)
```

#### Issue Anchor Linking
```
GET    /api/projects/{id}/anchors/{type}/{anchor_id}/issues    # Get issues for anchor
GET    /api/issues/{issue_key}/links                           # Get anchor links for issue
```

#### Application Integration
```
POST   /api/applications/launch           # Launch external application
POST   /api/applications/revizto-exporter # Run Revizto exporter
POST   /api/scripts/run-health-importer   # Execute health importer
POST   /api/file-browser/select-file      # File picker dialog
POST   /api/file-browser/select-folder    # Folder picker dialog
```

#### Logging & Monitoring
```
POST   /api/logs/frontend                 # Frontend error logging
```

**Note**: Many endpoints support query parameters for filtering, pagination, and sorting. See inline API documentation for details.

## 📊 Database Schema

The system uses a normalized SQL Server schema with comprehensive relational data model. All database access **MUST** use schema constants from `constants/schema.py` - never hardcode table or column names.

### Project Management Tables
- `Projects` - Project master data with metadata and configuration
- `ProjectServices` - Service definitions, pricing, and deliverables
- `ServiceTemplates` - Reusable service templates (JSON-based)
- `ReviewSchedule` - Review cycle scheduling with planned/actual dates
- `ReviewParameters` - Review configuration and deliverables per cycle
- `ProjectBookmarks` - User favorites for quick project access
- `ProjectAliases` - External system integration mappings
- `ProjectTypes` - Project type categorization

### Task & Resource Management Tables
- `Tasks` - Task tracking with dependencies, priorities, and status
- `TaskDependencies` - Predecessor/successor relationships
- `Milestones` - Project milestones and target dates
- `Users` - Team members with skills, roles, and hourly rates
- `ServiceAssignments` - User-to-service allocations
- `ReviewAssignments` - User-to-review allocations

### Billing & Financial Tables
- `BillingClaims` - Monthly billing claims with totals
- `BillingClaimLines` - Claim line items with progress tracking and amounts
- `ServiceItems` - Billable service items with rates

### Document Management Tables
- `Documents` - Document metadata and versioning
- `ReviewDeliverables` - Document-to-review associations
- `tblACCDocs` - ACC document synchronization data

### External Integration Tables
- `AccImportFolders` - ACC data folder paths per project
- `AccImportLogs` - ACC import history with timestamps and status
- `ReviztoProjectMappings` - Revizto project UUID mappings
- `ReviztoIssueAttributeMappings` - Custom attribute field mappings
- `ReviztoExtractionRuns` - Issue extraction run history

### Health & Quality Tables (RevitHealthCheckDB)
- `FileHealthMetrics` - Overall Revit file health scores
- `WarningMetrics` - Warning and error tracking
- `ElementMetrics` - Element counts and performance
- `NamingCompliance` - Naming convention validation results
- `GridAlignmentMetrics` - Cross-model grid alignment data
- `LevelAlignmentMetrics` - Level elevation coordination
- `ControlPoints` - Survey control point tracking

### ACC Integration Tables (acc_data_schema)
- `vw_issues_expanded_pm` - Main ACC issues view with all metadata
- `IssueCategories` - Issue categorization and classification
- `IssueCustomAttributes` - Custom attribute data

### Automation Tables
- `DynamoScripts` - Dynamo script library
- `DynamoJobs` - Batch processing job definitions
- `DynamoJobFiles` - Revit files associated with batch jobs
- `ControlModels` - Control model specifications for comparison

### Reference & Configuration Tables
- `ReferenceProjectTypes` - Project type definitions
- `ReferenceReviewStages` - Review stage templates
- `ReferenceTaskPriorities` - Task priority levels
- `Clients` - Client organization data
- `NamingConventions` - Project-specific naming rules

See [docs/database_schema.md](docs/database_schema.md) for complete schema documentation, entity relationships, and data dictionaries.

## 📁 Project Structure

```
BIMProjMngmt/
├── frontend/                   # React + TypeScript web application
│   ├── src/
│   │   ├── components/         # Reusable React components
│   │   ├── pages/              # Page components (routing)
│   │   ├── api/                # API client functions (Axios)
│   │   ├── App.tsx             # Root application component
│   │   └── main.tsx            # Application entry point
│   ├── package.json            # Frontend dependencies
│   └── vite.config.ts          # Vite build configuration
│
├── backend/                    # Flask API server
│   ├── app.py                  # Main Flask application (4700+ lines)
│   ├── logs/                   # Application logs
│   │   ├── app.log             # General Flask logs
│   │   ├── frontend.log        # Frontend error logs
│   │   └── warehouse.log       # Analytics query logs
│   └── documents/              # Document storage
│
├── database.py                 # Core database operations (legacy)
├── database_pool.py            # Connection pooling (100% migrated Oct 2025)
├── review_management_service.py # Review business logic
├── config.py                   # Environment configuration
├── requirements.txt            # Python dependencies
│
├── handlers/                   # Data import/export handlers
│   ├── acc_handler.py          # ACC ZIP import processor
│   ├── rvt_health_importer.py  # Revit health Excel importer
│   ├── process_ifc.py          # IFC model processor
│   └── ideate_health_exporter.py # Health data exporter
│
├── services/                   # External microservices
│   ├── revizto-dotnet/         # C# Revizto extraction service
│   ├── aps-auth-demo/          # APS OAuth authentication service
│   └── acc-node/               # ACC connector service (Node.js)
│
├── warehouse/                  # Analytics data warehouse
│   ├── dashboard_metrics.py    # Aggregated metrics queries
│   ├── issues_analytics.py     # Issue analysis functions
│   └── health_dashboards.py    # Model health analytics
│
├── constants/                  # Schema and configuration constants
│   ├── schema.py               # Database schema constants (CRITICAL)
│   └── naming_conventions/     # Naming convention definitions
│
├── sql/                        # Database scripts
│   ├── tables/                 # Table creation DDL
│   ├── views/                  # View definitions
│   ├── migrations/             # Schema migration scripts
│   └── stored_procedures/      # Stored procedure definitions
│
├── templates/                  # Service template JSON files
│   ├── SINSW-MPHS.json
│   ├── AWS-Day1.json
│   └── NEXTDC-S5.json
│
├── tests/                      # Test suite (pytest)
│   ├── test_review_management.py
│   ├── test_analytics_dashboard.py
│   ├── test_project_services.py
│   └── test_database.py
│
├── tools/                      # Maintenance and utility scripts
│   ├── db/                     # Database tools
│   │   ├── check_database_state.py
│   │   ├── verify_schema.py
│   │   └── migration_helpers.py
│   ├── imports/                # Import testing tools
│   ├── analytics/              # Analytics debugging
│   └── docs/                   # Documentation generators
│
├── scripts/                    # Operational scripts
│   ├── check_schema.py         # Schema validation and auto-fix
│   ├── cleanup_phase1.ps1      # Codebase organization cleanup
│   └── deploy_warehouse.py     # Warehouse deployment
│
├── docs/                       # Comprehensive documentation
│   ├── database_schema.md      # Database reference
│   ├── DATABASE_CONNECTION_GUIDE.md # ⭐ MANDATORY connection patterns
│   ├── REACT_INTEGRATION_ROADMAP.md # Frontend development plan
│   ├── ACC_SYNC_ARCHITECTURE.md     # ACC integration guide
│   ├── ISSUE_ANALYTICS_QUICKSTART.md # Analytics usage
│   ├── cleanup/                # Cleanup documentation
│   └── archive/                # Historical documentation
│
├── logs/                       # Root-level logs
├── infra/                      # Infrastructure configuration
├── shared/                     # Shared utilities
├── .github/                    # GitHub configuration
│   └── copilot-instructions.md # AI agent instructions
├── AGENTS.md                   # AI agent guidance
├── pytest.ini                  # Pytest configuration
└── README.md                   # This file
```

### Key File Responsibilities

| File/Directory | Purpose | Critical? |
|---------------|---------|-----------|
| `constants/schema.py` | **Database schema constants** - Never hardcode table/column names | ✅ YES |
| `database_pool.py` | **Connection pooling** - All new code must use this | ✅ YES |
| `backend/app.py` | **Main API server** - All REST endpoints defined here (5900+ lines) | ✅ YES |
| `frontend/src/api/` | **API client layer** - Axios calls to backend | ✅ YES |
| `config.py` | **Environment config** - Database credentials, service URLs | ✅ YES |
| `docs/DATABASE_CONNECTION_GUIDE.md` | **Mandatory reading** for all developers | ✅ YES |
| `handlers/*.py` | Data import processors (ACC, Revit Health, IFC) | ⚠️ Important |
| `warehouse/etl/pipeline.py` | Data warehouse orchestration and incremental loads | ⚠️ Important |
| `services/` | Business logic services and external microservices | ⚠️ Important |
| `sql/migrations/` | Database schema version control and migrations | ⚠️ Important |
| `tests/` | Automated test suite (pytest) | ⚠️ Important |
| `tools/` | Development and debugging utilities | 📘 Reference |

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

### Database Connection Management (MANDATORY)
**ALWAYS** use `database_pool.py` for all new code (100% migrated as of October 2025):

```python
from database_pool import get_db_connection

# ✅ CORRECT - Uses connection pooling
conn = get_db_connection()
try:
    cursor = conn.cursor()
    # ... operations ...
    conn.commit()
finally:
    conn.close()  # Returns connection to pool
```

**Read**: [docs/DATABASE_CONNECTION_GUIDE.md](docs/DATABASE_CONNECTION_GUIDE.md) - MANDATORY for all developers

## 🗺️ Roadmap & Development Status

See [docs/ROADMAP.md](docs/ROADMAP.md) for the detailed multi-phase development plan.

### Completed Features ✅ (2024-2025)
- ✅ React + TypeScript web frontend with Material-UI
- ✅ Connection pooling migration (October 2025)
- ✅ Core project and review management with cycles
- ✅ Enhanced task management with dependencies and Gantt
- ✅ Issue analytics dashboard with ML categorization
- ✅ Multi-source data integration (ACC, Revizto, Revit)
- ✅ Service templates and billing claim automation
- ✅ Project alias management and external mapping
- ✅ Real-time APS integration with OAuth
- ✅ Revit health monitoring and naming compliance
- ✅ Dynamo batch automation framework
- ✅ Warehouse analytics with dashboard metrics
- ✅ Coordinate alignment and control point tracking

### In Progress 🚧 (Q1-Q2 2026)
- 🚧 Advanced reporting engine with custom templates
- 🚧 Real-time collaboration and notifications
- 🚧 Enhanced issue pattern recognition and root cause analysis
- 🚧 Performance optimization and caching strategies
- 🚧 Comprehensive API documentation (OpenAPI/Swagger)
- 🚧 Bid performance analytics and historical trending
- 🚧 Anchor-based project portfolio analytics

### Planned Features 📋 (2026)
- 📋 AI-powered issue categorization and risk prediction
- 📋 Automated quality assurance workflows
- 📋 Mobile application companion (iOS/Android)
- 📋 Integration with additional BIM platforms (Navisworks, BIM 360)
- 📋 Advanced financial forecasting and resource optimization
- 📋 GraphQL API for flexible data queries
- 📋 Webhook support for external integrations
- 📋 Role-based access control (RBAC) and permissions
- 📋 Audit logging and compliance reporting

## 📖 Documentation

### Core Documentation
- [Database Schema](docs/database_schema.md) - Complete schema reference
### Core Documentation
- **[Database Schema](docs/database_schema.md)** - Complete schema reference with all tables and relationships
- **[DATABASE_CONNECTION_GUIDE.md](docs/DATABASE_CONNECTION_GUIDE.md)** ⭐ - **MANDATORY** reading for all developers
  - Connection pool usage (100% migrated October 2025)
  - Code examples and best practices
  - Migration patterns and troubleshooting
  - Performance optimization guidelines
- **[React Integration Roadmap](docs/REACT_INTEGRATION_ROADMAP.md)** - Complete frontend development plan
- **[ACC Sync Architecture](docs/ACC_SYNC_ARCHITECTURE.md)** - Autodesk Construction Cloud integration guide
- **[Issue Analytics Quickstart](docs/ISSUE_ANALYTICS_QUICKSTART.md)** - Analytics dashboard usage
- **[Review Management Overview](docs/enhanced_review_management_overview.md)** - Review workflow guide
- **[Implementation Complete](docs/IMPLEMENTATION_COMPLETE.md)** - System implementation details
- **[Roadmap](docs/ROADMAP.md)** - Development roadmap and future features

### Integration Guides
- [ACC Sync Quick Start](docs/ACC_SYNC_QUICK_START.md) - Getting started with ACC integration
- [ACC Sync Implementation Guide](docs/ACC_SYNC_IMPLEMENTATION_GUIDE.md) - Detailed ACC setup
- [Dynamo Batch Setup Guide](docs/DYNAMO_BATCH_SETUP_GUIDE.md) - Batch automation configuration
- [Custom Attributes Quick Reference](docs/CUSTOM_ATTRIBUTES_QUICK_REF.md) - ACC custom attributes
- [Data Imports Architecture](docs/DATA_IMPORTS_ARCHITECTURE.md) - Import system design

### Analytics & Dashboards
- [Analytics Dashboard Quick Reference](docs/ANALYTICS_DASHBOARD_QUICK_REF.md) - Dashboard usage
- [Analytics Dashboard Visual Guide](docs/ANALYTICS_DASHBOARD_VISUAL_GUIDE.md) - Visual walkthrough
- [Warehouse Metrics Guide](docs/ANALYTICS_DASHBOARD_DATA_SOURCE_REVIEW.md) - Data warehouse metrics
- [Issue Analytics Roadmap](docs/ISSUE_ANALYTICS_ROADMAP.md) - Analytics feature development

### Migration & Maintenance Reports
- [DB Migration Phase 4 Complete](docs/DB_MIGRATION_PHASE4_COMPLETE.md) - Latest migration (October 2025)
- [DB Migration Session 3](docs/DB_MIGRATION_SESSION3_COMPLETE.md) - Previous migration session
- [Database Migration Complete](docs/DATABASE_MIGRATION_COMPLETE.md) - Overall migration summary
- [DB Connection Quick Reference](docs/DB_CONNECTION_QUICK_REF.md) - Connection patterns
- [Comprehensive Test Report](docs/COMPREHENSIVE_TEST_REPORT.md) - Test suite results

### Development & Cleanup
- [Cleanup Summary](docs/cleanup/CLEANUP_SUMMARY.md) - Codebase organization status
- [Cleanup Quickstart](docs/cleanup/CLEANUP_QUICKSTART.md) - Start cleanup immediately
- [File Organization Guide](docs/cleanup/FILE_ORGANIZATION_GUIDE.md) - Organization rules

## 🛠️ Development Tools & Utilities

### Database Tools (`tools/db/`)
- `check_database_state.py` - Verify database connections and state
- `verify_schema.py` - Schema validation utilities
- `migration_helpers.py` - Database migration assistants

### Import Tools (`tools/imports/`)
- ACC import testing and validation
- Revit health import debugging
- IFC processing utilities

### Analytics Tools (`tools/analytics/`)
- Dashboard metric debugging
- Query performance analysis
- Data warehouse testing

### Documentation Tools (`tools/docs/`)
- Documentation link checker
- API documentation generators
- Schema documentation builders

## 🤝 Contributing & Development

This is a private project for construction project management. For collaboration or questions:

### Getting Started
1. Read [DEVELOPER_ONBOARDING.md](docs/DEVELOPER_ONBOARDING.md) for comprehensive onboarding
2. Review [DATABASE_CONNECTION_GUIDE.md](docs/DATABASE_CONNECTION_GUIDE.md) - **MANDATORY**
3. Understand [File Organization Guide](docs/cleanup/FILE_ORGANIZATION_GUIDE.md)
4. Set up development environment following Quick Start section above

### Code Standards
- Use schema constants from `constants/schema.py` - **NEVER** hardcode table/column names
- Use `database_pool.py` for all database connections
- Place test files in `tests/`, utilities in `tools/`, services in `services/`
- Follow TypeScript strict mode for frontend code
- Write unit tests for all business logic
- Document complex functions and API endpoints

### Pull Request Guidelines
1. Run `python -m pytest tests/` - ensure all tests pass
2. Run `python scripts/check_schema.py` - validate schema consistency
3. Update documentation if adding features
4. Follow existing code patterns and conventions

## 📄 License

Copyright © 2025 Rico Strinati. All rights reserved.

## 🆘 Support & Contact

For issues, questions, or feature requests:
1. **Documentation**: Check `/docs` directory for comprehensive guides
2. **Examples**: Review `/tests` for usage examples and patterns
3. **Issues**: Contact development team or repository owner
4. **Database Issues**: Consult [DATABASE_CONNECTION_GUIDE.md](docs/DATABASE_CONNECTION_GUIDE.md)
5. **API Questions**: See API Endpoints Reference section above

---

**Important**: This system manages real construction project workflows with financial and scheduling implications. Always verify database operations, validate data integrity, and test thoroughly before deploying changes to production.

**Last Updated**: January 2026
