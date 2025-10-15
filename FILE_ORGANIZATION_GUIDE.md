# BIM Project Management - File Organization Guide

> **Purpose:** Prevent future file clutter and maintain clean codebase structure  
> **Audience:** All developers  
> **Status:** Mandatory - enforced by pre-commit hooks

---

## 📁 Directory Structure Rules

### Root Directory - ONLY Essential Files

**Allowed files:**
```
✓ run_enhanced_ui.py              # Main application launcher
✓ database.py                     # Core database module
✓ config.py                       # Environment configuration
✓ review_management_service.py    # Core business logic service
✓ review_validation.py            # Core validation logic
✓ requirements.txt                # Python dependencies
✓ package.json                    # Node.js dependencies
✓ package-lock.json              # Node.js lock file
✓ pytest.ini                      # Pytest configuration
✓ .gitignore                      # Git ignore rules
✓ .editorconfig                   # Editor configuration
✓ README.md                       # Project overview
✓ CONTRIBUTING.md                 # Contribution guidelines
✓ LICENSE                         # License file
✓ setup_env.sh                    # Environment setup
✓ start-dev.ps1                   # Development launcher
✓ start-dev.sh                    # Development launcher (Unix)
✓ stop-servers.ps1               # Server shutdown script
```

**NOT allowed in root:**
```
✗ *_test.py, test_*.py           → Must go in /tests
✗ *.md (except README, CONTRIBUTING)  → Must go in /docs
✗ debug_*.py, check_*.py         → Must go in /tools
✗ phase*.py                      → Must go in /archive
✗ *.txt summaries                → Must go in /docs
```

---

## 🧪 /tests - All Test Files

### Structure
```
tests/
├── __init__.py
├── conftest.py                   # Pytest fixtures
├── README.md                     # Testing guide
├── integration/                  # Integration tests
│   ├── test_comprehensive.py
│   ├── test_critical_gaps.py
│   └── test_ui_alignment.py
├── unit/                         # Unit tests
│   ├── test_services/
│   │   ├── test_review_service.py
│   │   ├── test_issue_analytics_service.py
│   │   └── test_project_alias_service.py
│   ├── test_handlers/
│   │   ├── test_acc_handler.py
│   │   ├── test_rvt_health_importer.py
│   │   └── test_review_handler.py
│   └── test_database/
│       ├── test_database_connections.py
│       └── test_schema_validation.py
├── api/                          # API endpoint tests
│   ├── test_api.py
│   ├── test_acc_api.py
│   └── test_health_api.py
├── ui/                           # UI component tests
│   ├── test_ui_basic.py
│   ├── test_tab_*.py
│   └── test_ui_alignment.py
└── fixtures/                     # Test data
    ├── sample_acc_data.json
    ├── sample_rvt_health.json
    └── test_projects.sql
```

### Naming Convention
- **Integration tests:** `test_comprehensive*.py`, `test_*_integration.py`
- **Unit tests:** `test_<module_name>.py` (e.g., `test_database.py`)
- **API tests:** `test_*_api.py` or `test_api_*.py`
- **UI tests:** `test_ui_*.py`, `test_tab_*.py`

### File Header Template
```python
"""
Test module for <component name>

Tests: <brief description>
Coverage: <what's tested>
Dependencies: <test dependencies>
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now import project modules
from database import connect_to_db
# ... rest of imports
```

---

## 📚 /docs - All Documentation

### Structure
```
docs/
├── README.md                     # Docs navigation
├── DOCUMENTATION_INDEX.md        # Main index (auto-generated)
├── guides/                       # User/developer guides
│   ├── QUICK_START.md
│   ├── DEVELOPER_ONBOARDING.md
│   ├── DATABASE_GUIDE.md
│   ├── CUSTOM_ATTRIBUTES_GUIDE.md
│   ├── DATA_IMPORTS_GUIDE.md
│   ├── REVIEW_MANAGEMENT_GUIDE.md
│   └── ISSUE_ANALYTICS_GUIDE.md
├── api/                          # API documentation
│   ├── DATA_IMPORTS_API.md
│   ├── BACKEND_API.md
│   └── REST_ENDPOINTS.md
├── architecture/                 # Technical architecture
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── DATA_FLOW.md
│   ├── DATABASE_SCHEMA.md
│   └── COMPONENT_DIAGRAM.md
├── security/                     # Security documentation
│   ├── SECURITY_POLICY.md
│   └── INCIDENT_REPORTS.md
├── archive/                      # Historical documentation
│   ├── migrations/
│   │   └── DB_MIGRATION_*.md
│   ├── implementations/
│   │   └── IMPLEMENTATION_*.md
│   └── fixes/
│       └── *_FIX.md
└── ROADMAP.md                    # Project roadmap
```

### Naming Convention
- **Guides:** `<TOPIC>_GUIDE.md` (e.g., `DATABASE_GUIDE.md`)
- **Quick references:** `<TOPIC>_QUICK_REF.md`
- **API docs:** `<API_NAME>_API.md`
- **Architecture:** `<COMPONENT>_ARCHITECTURE.md`
- **Historical:** `<TOPIC>_<DATE>.md` (if date-specific)

### Document Header Template
```markdown
# <Title>

> **Last Updated:** YYYY-MM-DD  
> **Status:** [Draft | Active | Deprecated | Archived]  
> **Audience:** [Developers | Users | Admins | All]  
> **Related:** Links to related docs

## Overview

Brief description...

## Table of Contents

- [Section 1](#section-1)
- [Section 2](#section-2)

---
```

### Consolidation Rules
1. **One authoritative guide per topic** - No duplicates
2. **Quick refs max 3 pages** - Link to full guide
3. **Archive completed work** - Don't delete history
4. **Update index when adding** - Keep DOCUMENTATION_INDEX.md current

---

## 🛠️ /tools - Utility Scripts

### Structure
```
tools/
├── README.md                     # Tools documentation
├── analysis/                     # Analysis scripts
│   ├── analyze_attribute_relationships.py
│   ├── analyze_custom_attributes.py
│   ├── analyze_project_aliases.py
│   └── generate_analytics_report.py
├── database/                     # DB utilities
│   ├── check_database_schema.py
│   ├── check_schema_compatibility.py
│   ├── compare_source_vs_view.py
│   └── verify_*.py
├── debug/                        # Debug utilities
│   ├── debug_custom_attributes_json.py
│   ├── debug_template_lookup.py
│   ├── diagnose_revizto_data.py
│   └── diagnose_schema_error.py
├── migrations/                   # Data migration scripts
│   ├── migrate_database_connections.py
│   ├── migrate_issue_analytics.py
│   ├── bulk_migrate_db.py
│   └── deploy_*.py
├── setup/                        # Setup/seeding scripts
│   ├── create_pain_points_table.py
│   ├── create_templates.py
│   ├── seed_keywords.py
│   └── setup_issue_analytics.py
└── testing/                      # Test runners (NOT tests)
    ├── run_batch_processing.py
    └── run_custom_attributes_merge.py
```

### Naming Convention
- **Analysis:** `analyze_*.py`, `generate_*_report.py`
- **Database checks:** `check_*.py`, `verify_*.py`, `compare_*.py`
- **Debug:** `debug_*.py`, `diagnose_*.py`
- **Migrations:** `migrate_*.py`, `deploy_*.py`, `fix_*.py`
- **Setup:** `create_*.py`, `seed_*.py`, `setup_*.py`
- **Test runners:** `run_*.py` (actual tests go in /tests)

### Script Header Template
```python
"""
<Script Name> - Brief description

Purpose: What this script does
Usage: python tools/<category>/<script_name>.py [args]
Prerequisites: What needs to be set up first
Author: Name
Date: YYYY-MM-DD
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Imports
from database import connect_to_db
from config import get_config

def main():
    """Main execution function"""
    pass

if __name__ == "__main__":
    main()
```

---

## 🎨 /ui - UI Components

### Structure
```
ui/
├── __init__.py
├── README.md
├── base_layout.py                # Base UI components
├── status_bar.py
├── tooltips.py
├── ui_helpers.py
├── tab_project.py                # Tab implementations
├── tab_review.py
├── tab_data_imports.py
├── tab_issue_analytics.py
├── tab_validation.py
├── enhanced_data_imports_tab.py
├── enhanced_task_management.py
├── project_alias_tab.py
├── gantt_chart.py                # Specialized widgets
└── tasks_users_ui.py
```

### Rules
- One file per major UI component
- Name files `tab_*.py` for tab implementations
- Name files `<widget_name>.py` for reusable widgets
- Keep UI logic separate from business logic

---

## 🔧 /services - Business Logic

### Structure
```
services/
├── __init__.py
├── README.md
├── review_service.py
├── issue_analytics_service.py
├── issue_batch_processor.py
├── issue_categorizer.py
├── issue_text_processor.py
├── project_alias_service.py
└── test_services.py              # Service-level integration tests
```

### Rules
- Pure business logic, no UI code
- One service per domain area
- Clear separation of concerns
- Must have unit tests in `/tests/unit/test_services/`

---

## 📦 /handlers - Data Import/Export

### Structure
```
handlers/
├── __init__.py
├── acc_handler.py                # ACC data import
├── rvt_health_importer.py        # Revit health import
├── process_ifc.py                # IFC model processing
├── ideate_health_exporter.py     # Health data export
└── review_handler.py             # Review data handling
```

### Rules
- Handles external data sources
- One handler per data source type
- Must validate data before import
- Must have error handling and logging

---

## 🗄️ /sql - Database Scripts

### Structure
```
sql/
├── tables/                       # Table creation scripts
│   └── create_*.sql
├── views/                        # View creation scripts
│   └── create_vw_*.sql
├── migrations/                   # Schema migrations
│   └── YYYYMMDD_*.sql
├── queries/                      # Reusable queries
│   └── *.sql
├── merge_*.sql                   # ACC data merge scripts
└── *.sql                         # One-off scripts
```

### Naming Convention
- **Tables:** `create_<table_name>.sql` or `add_<table_name>.sql`
- **Views:** `create_vw_<view_name>.sql`
- **Migrations:** `YYYYMMDD_<description>.sql`
- **Merge scripts:** `merge_<source>_<table>.sql`

---

## 📜 /scripts - Build/Deploy Scripts

### Structure
```
scripts/
├── check_schema.py               # Schema validation
├── verify_schema.py              # Schema verification
├── cleanup_phase1.ps1            # Cleanup scripts
└── setup_environment.ps1         # Environment setup
```

### Rules
- **ONLY** build, deploy, or core maintenance scripts
- No test files
- No analysis scripts (those go in /tools)
- Must be executable

---

## 🔒 /constants - Configuration Constants

### Structure
```
constants/
├── __init__.py
├── schema.py                     # Database schema constants
└── config.py                     # Application constants
```

### Rules
- Never hardcode database identifiers
- Always import from constants
- Use descriptive constant names

---

## 📋 Decision Tree: Where Does This File Go?

```
New file created
    │
    ├─ Is it a test?
    │  └─ YES → /tests
    │      ├─ Tests one module → /tests/unit
    │      ├─ Tests multiple components → /tests/integration
    │      ├─ Tests API endpoints → /tests/api
    │      └─ Tests UI → /tests/ui
    │
    ├─ Is it documentation?
    │  └─ YES → /docs
    │      ├─ User guide → /docs/guides
    │      ├─ API reference → /docs/api
    │      ├─ Architecture → /docs/architecture
    │      ├─ Historical → /docs/archive
    │      └─ Security → /docs/security
    │
    ├─ Is it a utility script?
    │  └─ YES → /tools
    │      ├─ Analyzes data → /tools/analysis
    │      ├─ Checks database → /tools/database
    │      ├─ Debugs issues → /tools/debug
    │      ├─ Migrates data → /tools/migrations
    │      └─ Sets up data → /tools/setup
    │
    ├─ Is it UI code?
    │  └─ YES → /ui
    │      ├─ Tab component → tab_*.py
    │      └─ Reusable widget → <widget_name>.py
    │
    ├─ Is it business logic?
    │  └─ YES → /services
    │      └─ <domain>_service.py
    │
    ├─ Does it handle external data?
    │  └─ YES → /handlers
    │      └─ <source>_handler.py
    │
    ├─ Is it a SQL script?
    │  └─ YES → /sql
    │      ├─ Creates table/view → /sql/tables or /sql/views
    │      ├─ Migration → /sql/migrations
    │      └─ Reusable query → /sql/queries
    │
    ├─ Is it a constant definition?
    │  └─ YES → /constants
    │
    ├─ Is it a build/deploy script?
    │  └─ YES → /scripts
    │
    ├─ Is it a core application file?
    │  └─ YES → Root (if essential)
    │
    └─ Is it deprecated/old?
       └─ YES → /archive
```

---

## 🚫 Common Mistakes to Avoid

### ❌ DON'T: Put tests in root
```
BIMProjMngmt/
├── test_something.py            # WRONG
└── something_test.py            # WRONG
```

### ✅ DO: Put tests in /tests
```
BIMProjMngmt/
└── tests/
    └── test_something.py        # CORRECT
```

---

### ❌ DON'T: Put docs in root
```
BIMProjMngmt/
├── MY_FEATURE_COMPLETE.md       # WRONG
└── HOW_TO_USE_X.md              # WRONG
```

### ✅ DO: Put docs in /docs with proper structure
```
BIMProjMngmt/
└── docs/
    ├── guides/
    │   └── MY_FEATURE_GUIDE.md  # CORRECT
    └── archive/
        └── MY_FEATURE_COMPLETE.md  # If historical
```

---

### ❌ DON'T: Mix script types in tools
```
tools/
├── test_something.py            # WRONG - this is a test
├── check_schema.py              # WRONG - this is build script
└── README.md                    # WRONG - this is docs
```

### ✅ DO: Organize by purpose
```
tools/
└── database/
    └── check_schema_compatibility.py  # CORRECT

tests/
└── test_something.py            # CORRECT

docs/
└── tools/
    └── README.md                # CORRECT
```

---

## 🔍 Pre-Commit Checklist

Before committing code, verify:

- [ ] No test files in root directory
- [ ] No `*.md` files in root (except README, CONTRIBUTING)
- [ ] No debug/analysis scripts in root
- [ ] All utility scripts in appropriate `/tools` subdirectory
- [ ] Documentation in `/docs` with proper structure
- [ ] Constants used instead of hardcoded strings
- [ ] File has proper header comment
- [ ] Imports use correct paths
- [ ] Tests exist in `/tests` for new code

---

## 🤖 Automated Enforcement

**Pre-commit hook** (`.git/hooks/pre-commit`):
```bash
#!/bin/bash
# Check file organization

# Fail if test files in root
if git diff --cached --name-only | grep -E '^test_.*\.py$|.*_test\.py$'; then
    echo "ERROR: Test files must be in /tests directory"
    exit 1
fi

# Fail if markdown docs in root (except README, CONTRIBUTING)
if git diff --cached --name-only | grep -E '^[A-Z_]+\.md$' | grep -v -E '^(README|CONTRIBUTING)\.md$'; then
    echo "ERROR: Documentation must be in /docs directory"
    exit 1
fi

echo "File organization check passed"
```

---

## 📞 Questions?

- **Where should X go?** → Use the decision tree above
- **Can I make an exception?** → No, consistency is critical
- **File doesn't fit anywhere?** → Ask team lead
- **Found misplaced file?** → Move it and create PR

---

**Remember:** A clean codebase is a productive codebase! 🎉
