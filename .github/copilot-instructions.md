# BIM Project Management System

BIM Project Management System is a Python desktop application built with Tkinter that manages Building Information Modeling (BIM) projects. It integrates with SQL Server databases, Autodesk Construction Cloud (ACC), Revizto, and handles IFC files for construction project management workflows.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Environment Setup
- Install Python 3.12+ and required system packages:
  ```bash
  sudo apt-get update && sudo apt-get install -y python3-tk python3-pip
  ```
- Install all Python dependencies:
  ```bash
  pip3 install -r requirements.txt
  ```
  - Installation takes approximately 2-3 minutes. NEVER CANCEL.
  - Alternatively, install manually: `pip3 install pyodbc pandas tkcalendar dash plotly ifcopenshell sqlparse pywebview python-dateutil`

### Application Structure
- **Main entry points**: `app.py` (primary), `app-sss.py` (alternative UI structure)
- **Core modules**: `database.py`, `ui.py`, `review_handler.py`, `acc_handler.py`, `process_ifc.py`
- **External tools**: `tools/ReviztoDataExporter.exe` (Windows .NET application)
- **SQL scripts**: `sql/` directory contains merge scripts for various data tables

### Build and Validation
- **Module import validation** (~0.7 seconds):
  ```bash
  python3 -c "import database, ui, review_handler, acc_handler, process_ifc, gantt_chart, rvt_health_importer; print('All modules OK')"
  ```
- **Syntax validation** (~1 second):
  ```bash
  python3 -m py_compile *.py
  ```
  Note: `app-sss.py` has known syntax errors due to hyphenated import paths (`ui-ss`). This is expected.

### Running the Application
- **GUI Application** (requires display):
  ```bash
  # For virtual display testing:
  Xvfb :99 -screen 0 1024x768x24 &
  DISPLAY=:99 python3 app.py
  ```
- **Expected startup behavior**: 
  - Database connection will fail without SQL Server (`P-NB-USER-028\SQLEXPRESS`)
  - UI will show database connection errors but should not crash entirely
  - Application startup takes ~0.4 seconds for Tkinter initialization

### Database Requirements
- **SQL Server**: Application expects `P-NB-USER-028\SQLEXPRESS` with databases:
  - `ProjectManagement` (primary database)
  - `RevitHealthCheckDB` (health data imports)
- **Database operations**: Insert projects, manage review schedules, import ACC data, process IFC files
- **Connection failures are normal** in development environments without SQL Server

## Validation Scenarios

After making changes, always test these core workflows:

### 1. Module Import Test
```bash
python3 -c "
import database
import ui  
import review_handler
import acc_handler
print('✅ Core modules import successfully')
"
```

### 2. Database Connection Handling
```bash
python3 -c "
import database
conn = database.connect_to_db()
if conn is None:
    print('✅ Database connection properly handles failure')
else:
    print('❌ Unexpected database connection success')
"
```

### 3. UI Module Loading (with virtual display)
```bash
# Requires display
DISPLAY=:99 python3 -c "
import tkinter as tk
import ui
root = tk.Tk()
root.withdraw()
print('✅ UI module loads without errors')
root.destroy()
"
```

## Common Tasks

### Development Workflow
1. **Always validate syntax first**: `python3 -m py_compile *.py`
2. **Test module imports**: Run import validation above
3. **For UI changes**: Test with virtual display
4. **For database changes**: Review connection strings and error handling

### File Structure Reference
```
.
├── app.py                 # Main application entry point
├── app-sss.py            # Alternative UI (has syntax errors - expected)
├── database.py           # Database connection and operations
├── ui.py                 # Main UI components (30KB+)
├── review_handler.py     # Review schedule management
├── acc_handler.py        # Autodesk Construction Cloud integration
├── process_ifc.py        # IFC file processing
├── gantt_chart.py        # Gantt chart visualization
├── rvt_health_importer.py # Revit health data import
├── tasks_users_ui.py     # Task and user management UI
├── requirements.txt      # Python dependencies (now populated)
├── sql/                  # SQL merge scripts for data import
├── tools/                # External .NET tools (Windows only)
│   ├── ReviztoDataExporter.exe
│   └── appsettings.json
├── ui-ss/               # Alternative UI structure
└── logs/                # Application logs
```

### Key Dependencies and Their Purposes
- **pyodbc**: SQL Server database connectivity
- **tkinter**: GUI framework (system package: python3-tk)
- **pandas**: Data manipulation for imports/exports
- **tkcalendar**: Date picker widgets
- **dash + plotly**: Web-based charts and dashboards
- **ifcopenshell**: IFC file format processing
- **pywebview**: Embedded web views for charts

### Timing Expectations
- **Module imports**: 0.7 seconds - NEVER CANCEL before 5 seconds
- **Tkinter initialization**: 0.4 seconds
- **Dependency installation**: 2-3 minutes - NEVER CANCEL, set timeout to 300+ seconds
- **GUI application startup**: 1-2 seconds (may fail on database connection)

### External Tool Integration
- **ReviztoDataExporter.exe**: Windows-only .NET application for Revizto API integration
- **Cannot be executed in Linux environments** - document this limitation
- **Configuration**: `tools/appsettings.json` contains API tokens and connection strings

### Known Limitations
- **SQL Server dependency**: Application requires specific SQL Server instance
- **Windows tools**: Some functionality requires Windows environment for .NET executables
- **Display requirement**: GUI components need X11 display (use Xvfb for testing)
- **Syntax errors in app-sss.py**: Expected due to hyphenated module names in ui-ss/ directory

### Error Handling Validation
Always verify your changes handle these expected error conditions:
- Database connection failures (most common in dev environments)
- Missing file paths for project folders
- GUI initialization without display
- Import errors for optional dependencies

When making changes:
1. Test all code paths with missing database connections
2. Verify GUI components handle missing data gracefully
3. Ensure file operations include proper error checking
4. Test module imports work in isolation