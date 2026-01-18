# Phase 1B: Database Migration Guide

**Date**: January 16, 2026  
**Scope**: Create ExpectedModels and ExpectedModelAliases tables  
**Duration**: < 5 minutes

---

## Pre-Migration Checklist

- [ ] Database backups are current
- [ ] No active queries against ProjectManagement.dbo
- [ ] Have admin credentials for SQL Server (default: admin02 / 1234)
- [ ] Running on `.\SQLEXPRESS` (or update server in steps below)

---

## Step 1: Backup Database (Recommended)

```powershell
# Using SQL Server Management Studio (recommended) or command line:
sqlcmd -S .\SQLEXPRESS -U admin02 -P 1234 -Q "BACKUP DATABASE [ProjectManagement] TO DISK = 'C:\Backups\ProjectManagement_pre_phase1b.bak';"
```

---

## Step 2: Run Migration Script

### Option A: Command Line (sqlcmd)

```powershell
cd c:\Users\RicoStrinati\Documents\research\BIMProjMngmt
sqlcmd -S .\SQLEXPRESS -U admin02 -P 1234 -d ProjectManagement -i sql\migrations\phase1b_create_expected_models_tables.sql
```

### Option B: SQL Server Management Studio

1. Open SQL Server Management Studio
2. Connect to `.\SQLEXPRESS` with admin02 / 1234
3. Select database: `ProjectManagement`
4. Open file: `sql\migrations\phase1b_create_expected_models_tables.sql`
5. Click **Execute** (F5)

### Option C: Python Script

```python
import subprocess
result = subprocess.run([
    'sqlcmd',
    '-S', '.\\SQLEXPRESS',
    '-U', 'admin02',
    '-P', '1234',
    '-d', 'ProjectManagement',
    '-i', 'sql\\migrations\\phase1b_create_expected_models_tables.sql'
], capture_output=True, text=True)

print(result.stdout)
if result.stderr:
    print("ERRORS:", result.stderr)
```

---

## Step 3: Verify Migration Success

You should see output like:

```
✅ Created table: dbo.ExpectedModels
✅ Created table: dbo.ExpectedModelAliases
✅ Phase 1B: Table creation complete

Next steps:
1. Run check_schema.py to verify schema constants match DB structure
2. Implement Phase 1C: Update get_model_register() for mode=expected
3. Create Phase 1E endpoints: CRUD for expected models and aliases
```

### Verify in SQL

```sql
-- Check tables exist
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME IN ('ExpectedModels', 'ExpectedModelAliases');

-- Check ExpectedModels columns
EXEC sp_help 'dbo.ExpectedModels';

-- Check ExpectedModelAliases columns
EXEC sp_help 'dbo.ExpectedModelAliases';

-- Verify indexes
SELECT * FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.ExpectedModelAliases');
```

---

## Step 4: Update Schema Constants

```bash
cd c:\Users\RicoStrinati\Documents\research\BIMProjMngmt
python check_schema.py --autofix --update-constants
```

Expected output:

```
✅ Schema verification complete
✅ Constants updated: constants/schema.py
```

---

## Step 5: Test Database Functions

```python
# In Python REPL or test script
from database import get_expected_models, get_expected_model_aliases
from database_pool import get_db_connection

# Test: Get expected models for project 2
models = get_expected_models(2)
print(f"✅ Found {len(models)} expected models for project 2")
# Should return: 0 (empty, waiting for manual or auto seeding)

# Test: Get aliases
aliases = get_expected_model_aliases(2)
print(f"✅ Found {len(aliases)} aliases for project 2")
# Should return: 0 (empty initially)
```

---

## Troubleshooting

### Error: "Cannot find file phase1b_create_expected_models_tables.sql"

**Solution**: Ensure you're in the correct directory:
```powershell
cd c:\Users\RicoStrinati\Documents\research\BIMProjMngmt
ls sql\migrations\phase1b*.sql  # Should show the file
```

### Error: "Login failed for user 'admin02'"

**Solution**: Verify credentials in config.py:
```python
from config import Config
print(f"DB_SERVER: {Config.DB_SERVER}")
print(f"DB_USER: {Config.DB_USER}")
print(f"DB_DRIVER: {Config.DB_DRIVER}")
```

### Error: "UNIQUE constraint violation"

**Solution**: Tables already exist. This is OK - the script checks for existing tables.
```sql
-- Drop tables if you need to re-run (careful!)
DROP TABLE dbo.ExpectedModelAliases;
DROP TABLE dbo.ExpectedModels;
-- Then re-run the migration
```

### Error: "Foreign key constraint ... invalid"

**Solution**: Ensure Projects and clients tables exist:
```sql
SELECT COUNT(*) FROM dbo.Projects;
SELECT COUNT(*) FROM dbo.clients;
```

If either returns 0, check database setup.

---

## Rollback (If Needed)

```sql
-- Drop new tables
DROP TABLE IF EXISTS dbo.ExpectedModelAliases;
DROP TABLE IF EXISTS dbo.ExpectedModels;

-- Remove from schema.py (revert to previous version)
git checkout constants/schema.py

-- Done - database returned to pre-Phase1B state
```

---

## Post-Migration Verification

### 1. Check table structure matches schema constants

```python
from constants import schema as S
print(S.ExpectedModels.TABLE)  # Should print: ExpectedModels
print(S.ExpectedModels.EXPECTED_MODEL_ID)  # Should print: expected_model_id
print(S.ExpectedModelAliases.MATCH_TYPE)  # Should print: match_type
```

### 2. Create test expected model

```python
from database import create_expected_model

test_id = create_expected_model(
    project_id=2,
    expected_model_key='TEST-MEP-00',
    display_name='Test MEP Core',
    discipline='MEP',
    is_required=True
)
print(f"✅ Created test expected model: {test_id}")
```

### 3. Test alias creation

```python
from database import create_expected_model_alias

alias_id = create_expected_model_alias(
    expected_model_id=test_id,
    project_id=2,
    alias_pattern='test-mep-core.rvt',
    match_type='exact',
    target_field='filename'
)
print(f"✅ Created test alias: {alias_id}")
```

### 4. Test expected mode endpoint

```bash
curl "http://localhost:5000/api/projects/2/quality/register?mode=expected" | python -m json.tool
```

Expected response:
```json
{
  "expected_rows": [
    {
      "expected_model_id": 1,
      "expected_model_key": "TEST-MEP-00",
      ...
    }
  ],
  "unmatched_observed": [...],
  "counts": {
    "expected_total": 1,
    "expected_missing": 1,
    "unmatched_total": 12,
    "attention_count": 13
  }
}
```

---

## Performance Notes

- Table creation: < 1 second
- Index creation: < 1 second  
- Foreign key constraints: < 1 second
- No data migration needed (tables start empty)
- No impact on existing observed-mode queries

---

## Success Criteria

✅ All of the following must be true:

1. [ ] `dbo.ExpectedModels` table exists with 9 columns
2. [ ] `dbo.ExpectedModelAliases` table exists with 8 columns
3. [ ] Schema constants updated (S.ExpectedModels, S.ExpectedModelAliases)
4. [ ] Both tables have correct indexes
5. [ ] Foreign key constraints validated
6. [ ] Database functions return empty lists (no data yet)
7. [ ] Endpoint `?mode=expected` returns expected response shape

---

**Status**: ✅ Ready to deploy  
**Timeline**: < 5 minutes to complete migration  
**Risk Level**: 🟢 LOW - Additive only, no breaking changes  
**Rollback**: Easy - drop 2 tables, revert schema.py
