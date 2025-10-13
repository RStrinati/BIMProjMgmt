# Developer Onboarding - Database & Frontend Guide

**Welcome to the BIM Project Management System development team!** 👋

This guide will get you up to speed on our database connection standards and the upcoming React frontend integration.

---

## 🎯 What You Need to Know

### 1. Database Connection Standard (MANDATORY)

**Status**: ✅ **Production Standard** (100% migrated as of October 2025)

**Quick Facts**:
- 🔒 **ALL database code** must use the connection pool pattern
- 📈 **44% performance improvement** over old pattern
- 🛡️ **Zero connection leaks** (automatic cleanup)
- 📉 **29% code reduction** (cleaner, more maintainable)

**Read This First**:
1. **Quick Reference**: [DB_CONNECTION_QUICK_REF.md](./DB_CONNECTION_QUICK_REF.md) - Print and keep handy!
2. **Complete Guide**: [DATABASE_CONNECTION_GUIDE.md](./DATABASE_CONNECTION_GUIDE.md) - Comprehensive patterns and examples

**The Golden Rule**:
```python
# ✅ ALWAYS DO THIS
from database_pool import get_db_connection
from constants import schema as S

def your_function():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT {S.Table.COL} FROM {S.Table.TABLE}")
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error: {e}")
        return []

# ❌ NEVER DO THIS
from database import connect_to_db  # ❌ DEPRECATED!
conn = connect_to_db()              # ❌ Manual connection
if conn is None:                     # ❌ Manual null check
    return
conn.close()                         # ❌ Manual cleanup
```

---

### 2. React Frontend Integration (IN PROGRESS)

**Status**: 🚧 **Planning Complete, Implementation Starting**

**Quick Facts**:
- 🎯 **4-6 month timeline** to production
- 🔧 **30+ API endpoints** already exist
- 📱 **Vite + React + TypeScript** (recommended stack)
- 🔄 **Parallel operation** with Tkinter during transition

**Read This First**:
1. **Roadmap**: [REACT_INTEGRATION_ROADMAP.md](./REACT_INTEGRATION_ROADMAP.md) - Complete implementation plan
2. **API Blockers**: [FRONTEND_INTEGRATION_BLOCKERS.md](./FRONTEND_INTEGRATION_BLOCKERS.md) - Known issues and gaps

**Timeline Overview**:
- **Phase 1 (Weeks 1-4)**: Project setup, API client, first component
- **Phase 2 (Weeks 5-10)**: Core features (projects, reviews, tasks)
- **Phase 3 (Weeks 11-16)**: Advanced features (analytics, imports)
- **Phase 4 (Weeks 17-20)**: Production readiness (auth, testing)
- **Phase 5 (Weeks 21-24)**: Deployment and user migration

---

## 📚 Essential Documentation

### Core Documentation
| Document | Purpose | When to Use |
|----------|---------|-------------|
| [DATABASE_CONNECTION_GUIDE.md](./DATABASE_CONNECTION_GUIDE.md) | Complete database patterns | Writing any database code |
| [DB_CONNECTION_QUICK_REF.md](./DB_CONNECTION_QUICK_REF.md) | Quick reference card | Daily reference |
| [REACT_INTEGRATION_ROADMAP.md](./REACT_INTEGRATION_ROADMAP.md) | Frontend implementation plan | Frontend development |
| [database_schema.md](./database_schema.md) | Database schema reference | Understanding data structure |

### Migration Reports
| Document | Content |
|----------|---------|
| [DB_MIGRATION_PHASE4_COMPLETE.md](./DB_MIGRATION_PHASE4_COMPLETE.md) | October 2025 migration (73 connections) |
| [DB_MIGRATION_SESSION3_COMPLETE.md](./DB_MIGRATION_SESSION3_COMPLETE.md) | Session 3 migration (39 connections) |
| [DATABASE_MIGRATION_COMPLETE.md](./DATABASE_MIGRATION_COMPLETE.md) | Overall migration summary (~191 connections) |

---

## 🚀 Getting Started

### Day 1: Setup Your Environment

1. **Clone and setup**
   ```bash
   git clone https://github.com/RStrinati/BIMProjMgmt.git
   cd BIMProjMgmt
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment**
   Create `.env` file:
   ```bash
   DB_SERVER=your-server-name
   DB_USER=your-username
   DB_PASSWORD=your-password
   DB_DRIVER={ODBC Driver 18 for SQL Server}
   PROJECT_MGMT_DB=ProjectManagement
   ACC_DB=acc_data_schema
   REVIT_HEALTH_DB=RevitHealthCheckDB
   ```

3. **Verify database connection**
   ```bash
   python -c "from database_pool import get_db_connection; \
              with get_db_connection() as conn: print('✅ Connected')"
   ```

4. **Run the application**
   ```bash
   python run_enhanced_ui.py
   ```

---

### Day 2: Learn the Patterns

**Morning**: Read database documentation
- [ ] Read [DB_CONNECTION_QUICK_REF.md](./DB_CONNECTION_QUICK_REF.md) (10 min)
- [ ] Skim [DATABASE_CONNECTION_GUIDE.md](./DATABASE_CONNECTION_GUIDE.md) (30 min)
- [ ] Review `constants/schema.py` (understand schema constants)

**Afternoon**: Review example code
- [ ] Look at `database.py` - core database functions
- [ ] Study `handlers/acc_handler.py` - data import example
- [ ] Review `services/project_alias_service.py` - service layer pattern
- [ ] Check `ui/project_tab.py` - UI integration example

---

### Day 3: Write Your First Code

**Exercise**: Create a simple function following the standard pattern

```python
# my_first_function.py
from database_pool import get_db_connection
from constants import schema as S
import logging

logger = logging.getLogger(__name__)

def get_active_projects():
    """Fetch all active projects from database.
    
    Returns:
        list: List of tuples (project_id, project_name)
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = f"""
                SELECT {S.Projects.ID}, {S.Projects.NAME}
                FROM {S.Projects.TABLE}
                WHERE {S.Projects.STATUS} = 'Active'
                ORDER BY {S.Projects.NAME}
            """
            cursor.execute(query)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching active projects: {e}")
        return []

# Test it
if __name__ == "__main__":
    projects = get_active_projects()
    for pid, pname in projects:
        print(f"{pid}: {pname}")
```

**Checklist**:
- [ ] Uses `get_db_connection()` context manager
- [ ] Uses schema constants (`S.Projects.*`)
- [ ] Has try/except error handling
- [ ] Returns sensible default on error
- [ ] Includes logging
- [ ] Has docstring

---

## 🎓 Learning Path

### Week 1: Database Fundamentals
- **Day 1**: Environment setup
- **Day 2**: Database connection patterns
- **Day 3**: Schema constants and basic queries
- **Day 4**: Write operations and transactions
- **Day 5**: Error handling and testing

### Week 2: Application Architecture
- **Day 1**: Tkinter UI structure
- **Day 2**: Service layer patterns
- **Day 3**: Data import handlers
- **Day 4**: Flask API endpoints
- **Day 5**: Review management system

### Week 3: Advanced Topics
- **Day 1**: Batch operations and performance
- **Day 2**: Multiple database integration
- **Day 3**: Testing strategies
- **Day 4**: Analytics and reporting
- **Day 5**: Deployment and operations

### Week 4: Frontend (If Applicable)
- **Day 1**: React project structure
- **Day 2**: TypeScript type definitions
- **Day 3**: API client integration
- **Day 4**: Component development
- **Day 5**: Testing and debugging

---

## 📋 Code Review Checklist

Before submitting code for review, verify:

### Database Code
- [ ] Uses `from database_pool import get_db_connection`
- [ ] Uses context manager: `with get_db_connection() as conn:`
- [ ] No manual null checks: ~~`if conn is None`~~
- [ ] No manual cleanup: ~~`conn.close()`~~
- [ ] Uses schema constants: `from constants import schema as S`
- [ ] No hardcoded table/column names
- [ ] Parameterized queries: `cursor.execute("... WHERE id = ?", (id,))`
- [ ] Calls `conn.commit()` after writes
- [ ] Has try/except error handling
- [ ] Has logging for errors
- [ ] Returns sensible default on error
- [ ] Minimizes connection scope (releases ASAP)

### General Code Quality
- [ ] Has docstrings
- [ ] Has type hints (for Python 3.10+)
- [ ] Follows PEP 8 style guide
- [ ] No commented-out code
- [ ] Has unit tests (if applicable)
- [ ] No security vulnerabilities (no string concatenation in SQL!)

---

## 🧪 Testing Your Code

### Unit Test Example

```python
# tests/test_my_function.py
import pytest
from unittest.mock import patch, MagicMock
from my_module import get_active_projects

def test_get_active_projects():
    """Test get_active_projects returns expected data."""
    # Create mock connection and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    # Mock query results
    mock_cursor.fetchall.return_value = [
        (1, 'Project A'),
        (2, 'Project B'),
    ]
    
    # Patch get_db_connection
    with patch('my_module.get_db_connection') as mock_get_conn:
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        
        # Run function
        result = get_active_projects()
        
        # Assertions
        assert len(result) == 2
        assert result[0][1] == 'Project A'
        mock_cursor.execute.assert_called_once()

def test_get_active_projects_error_handling():
    """Test error handling returns empty list."""
    with patch('my_module.get_db_connection') as mock_get_conn:
        mock_get_conn.return_value.__enter__.side_effect = Exception("DB Error")
        
        result = get_active_projects()
        
        assert result == []
```

Run tests:
```bash
pytest tests/test_my_function.py -v
```

---

## ⚠️ Common Pitfalls

### 1. Forgetting to Commit
```python
# ❌ WRONG - Changes won't persist!
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("UPDATE ...")
    # Missing conn.commit()!

# ✅ CORRECT
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("UPDATE ...")
    conn.commit()  # ← Don't forget!
```

### 2. Hardcoding Table Names
```python
# ❌ WRONG
cursor.execute("SELECT * FROM tblProjects")

# ✅ CORRECT
from constants import schema as S
cursor.execute(f"SELECT {S.Projects.ID} FROM {S.Projects.TABLE}")
```

### 3. SQL Injection Risk
```python
# ❌ WRONG - SECURITY RISK!
name = request.form['name']
cursor.execute(f"SELECT * FROM table WHERE name = '{name}'")

# ✅ CORRECT - Parameterized query
name = request.form['name']
cursor.execute("SELECT * FROM table WHERE name = ?", (name,))
```

### 4. Holding Connection Too Long
```python
# ❌ WRONG - Connection held during long processing
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT ...")
    data = cursor.fetchall()
    
    # Long processing (connection idle!)
    for row in data:
        time.sleep(1)
        complex_processing(row)

# ✅ CORRECT - Release connection quickly
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT ...")
    data = cursor.fetchall()

# Connection released, now process
for row in data:
    time.sleep(1)
    complex_processing(row)
```

---

## 🆘 Getting Help

### Resources
1. **Documentation**: Check `docs/` directory first
2. **Example Code**: Look at recently migrated files
3. **Tests**: Review `tests/` for usage examples
4. **Schema**: Check `constants/schema.py` for table/column names

### Ask for Help
If stuck:
1. Check the documentation (most questions are answered there)
2. Look at similar code in the codebase
3. Ask a team member
4. Create a GitHub issue (if applicable)

### Common Questions

**Q: Which database should I connect to?**  
A: Default is `ProjectManagement`. Use `get_db_connection('acc_data_schema')` or `get_db_connection('RevitHealthCheckDB')` for other databases.

**Q: Do I need to close the connection?**  
A: No! The context manager (`with` statement) handles cleanup automatically.

**Q: What if I need to use the old `connect_to_db()`?**  
A: You don't. It's deprecated. Always use `get_db_connection()`.

**Q: How do I run multiple queries in a transaction?**  
A: Execute all queries in one `with` block and call `conn.commit()` once at the end.

**Q: Can I store a connection as an instance variable?**  
A: No! Never store connections. Get a new connection each time you need one.

---

## 🎯 Success Criteria

After your first week, you should be able to:

- [ ] Set up the development environment
- [ ] Connect to the database using the connection pool
- [ ] Write a simple read query using schema constants
- [ ] Write a function that inserts data (with commit)
- [ ] Handle errors properly
- [ ] Write a unit test for your code
- [ ] Understand the Tkinter UI structure
- [ ] Understand the Flask API endpoints
- [ ] Know where to find documentation

After your first month, you should be able to:

- [ ] Implement a complete feature (UI + database + API)
- [ ] Write batch operations efficiently
- [ ] Work with multiple databases
- [ ] Optimize database queries
- [ ] Debug connection pool issues
- [ ] Review other developers' code
- [ ] Contribute to the React frontend (if applicable)

---

## 📊 Project Statistics

**Database Migration** (October 2025):
- ✅ **191 connections migrated** (100%)
- ✅ **98 files updated**
- ✅ **44% average performance improvement**
- ✅ **29% code reduction**
- ✅ **Zero connection leaks**

**Codebase**:
- **3 databases**: ProjectManagement, acc_data_schema, RevitHealthCheckDB
- **30+ API endpoints**: REST API for frontend
- **8+ UI tabs**: Tkinter desktop application
- **50+ database functions**: Core data access layer
- **100+ schema constants**: Type-safe database access

---

## 🚀 Next Steps

**Ready to contribute?**

1. ✅ **Setup environment** (see "Getting Started")
2. ✅ **Read database guide** (mandatory!)
3. ✅ **Review example code** (see Day 2)
4. ✅ **Write your first function** (see Day 3)
5. ✅ **Get code reviewed** (use checklist)
6. ✅ **Join frontend development** (if interested)

**Questions?** Check the docs or ask the team!

---

**Welcome aboard! Let's build great software together! 🚀**

---

**Document Created**: October 13, 2025  
**Last Updated**: October 13, 2025  
**Maintained By**: Development Team  
**Next Review**: January 2026
