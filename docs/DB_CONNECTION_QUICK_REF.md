# Database Connection Quick Reference Card

**Print this and keep at your desk! 📄**

---

## ✅ CORRECT Pattern (Always Use This)

```python
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
```

---

## ❌ NEVER Do This

```python
# ❌ NO manual connection
conn = connect_to_db()

# ❌ NO manual null checks
if conn is None:
    return

# ❌ NO manual cleanup
conn.close()

# ❌ NO hardcoded table names
cursor.execute("SELECT * FROM tblProjects")
```

---

## 🔑 Key Rules

1. **ALWAYS** use `with get_db_connection() as conn:`
2. **ALWAYS** commit writes: `conn.commit()`
3. **ALWAYS** use schema constants: `S.Table.COLUMN`
4. **ALWAYS** use parameterized queries: `cursor.execute("... WHERE id = ?", (id,))`
5. **ALWAYS** handle exceptions with try/except
6. **ALWAYS** minimize connection scope (release ASAP)

---

## 📋 Common Patterns

### Read-Only Query
```python
try:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT ...")
        return cursor.fetchall()
except Exception as e:
    logger.error(f"Error: {e}")
    return []
```

### Write Operation
```python
try:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT ...")
        conn.commit()  # ← CRITICAL!
        return True
except Exception as e:
    logger.error(f"Error: {e}")
    return False
```

### Batch Operation
```python
try:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany("INSERT ...", params)
        conn.commit()
        return True
except Exception as e:
    logger.error(f"Error: {e}")
    return False
```

### Multiple Databases
```python
try:
    # Database 1
    with get_db_connection('Database1') as conn1:
        cursor = conn1.cursor()
        cursor.execute("SELECT ...")
        data = cursor.fetchall()
    
    # Database 2
    with get_db_connection('Database2') as conn2:
        cursor = conn2.cursor()
        cursor.executemany("INSERT ...", data)
        conn2.commit()
    
    return True
except Exception as e:
    logger.error(f"Error: {e}")
    return False
```

---

## ⚠️ Common Mistakes

| Mistake | Fix |
|---------|-----|
| Forgot `conn.commit()` | Data won't persist! Always commit writes |
| Using `SELECT *` | Specify columns: `SELECT col1, col2` |
| Hardcoded table names | Use schema constants: `S.Table.NAME` |
| String concatenation in SQL | Use parameterized queries: `?` |
| Holding connection too long | Minimize `with` block scope |
| Not handling exceptions | Always use try/except |

---

## 🧪 Testing Your Code

```python
# Mock for unit tests
from unittest.mock import patch, MagicMock

def test_your_function():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [(1, 'Test')]
    
    with patch('your_module.get_db_connection') as mock_get:
        mock_get.return_value.__enter__.return_value = mock_conn
        
        result = your_function()
        
        assert len(result) == 1
        mock_cursor.execute.assert_called_once()
```

---

## 🔧 Troubleshooting

**Connection pool exhausted?**
→ Reduce connection hold time, increase `MAX_POOL_SIZE`

**Stale data?**
→ Did you call `conn.commit()`?

**Memory leak?**
→ Check you're using context manager (`with` statement)

**Database deadlock?**
→ Lock tables in consistent order, keep transactions short

---

## 📚 Full Documentation

See: `docs/DATABASE_CONNECTION_GUIDE.md`

---

**Last Updated**: October 13, 2025  
**Status**: Production Standard (100% Migrated)  
**Questions?** Check docs or ask the team!
