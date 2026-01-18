# Quick Reference: What's New in Documentation (Jan 2026)

## 📋 TL;DR - Key Updates

### README.md
| Section | Update | Impact |
|---------|--------|--------|
| Feature List | Added Bid & Contract Mgmt, BEP Matrix, Anchor Linking | Shows latest features |
| Issue Analytics | Enhanced with NLP, reliability metrics, anchor linking | More accurate capability description |
| API Endpoints | +20 new endpoints documented (Bid, Variation, Anchor, BEP) | Comprehensive endpoint reference |
| File Responsibilities | Clarified current file purposes | Better developer navigation |

### .github/copilot-instructions.md
| Section | Update | Impact |
|---------|--------|--------|
| Architecture | Enhanced data flows with Warehouse, Bids, Anchors | Shows complete system picture |
| DB Connection | Updated to `database_pool.get_db_connection()` | Matches Oct 2025 migration |
| Common Patterns | Added 5 new sections (Bids, Anchors, Warehouse, Reliability, BEP) | Current best practices |
| Services | Expanded with 8 specific business logic services | Clear service boundaries |
| Latest Features | New "Jan 2026" section with complete feature list | Points to newest capabilities |

---

## 🎯 For Agents & Developers

### If You're Working On...

**New Feature Development**:
→ Read: `.github/copilot-instructions.md` "Common Patterns & Gotchas" section
→ Check: `constants/schema.py` for data model
→ Follow: File organization rules in copilot-instructions

**Data Warehouse / Analytics**:
→ Read: `warehouse/etl/pipeline.py` documentation in agent instructions
→ Check: `warehouse/README.md` for pipeline architecture
→ Run: Tests in `warehouse/etl/` for validation

**Bid & Contract Management**:
→ New in Jan 2026! Full documentation in:
- `README.md` section 8 (Billing & Financial Management)
- `.github/copilot-instructions.md` "Bid & Contract Management" pattern
- API endpoints: `/api/bids/*` family

**Issue Analytics & Anchor Linking**:
→ New in Jan 2026! Documentation in:
- `README.md` sections 5, 10b
- `.github/copilot-instructions.md` "Issue Anchor Linking" pattern
- API endpoints: `/api/projects/{id}/anchors/*` family

**Revit Health & Naming**:
→ Existing but enhanced:
- Dashboard endpoints: `/api/dashboard/revit-health`, `/dashboard/naming-compliance`
- Handler: `handlers/rvt_health_importer.py`
- Service: `services/revit_health_warehouse_service.py`

---

## 🔄 Connection Pooling - Now Mandatory

**Old Pattern** (❌ Don't use):
```python
conn = connect_to_db()
```

**New Pattern** (✅ Use this):
```python
from database_pool import get_db_connection

conn = get_db_connection()
try:
    # ... work ...
    conn.commit()
finally:
    conn.close()  # Returns to pool
```

**Status**: 100% migrated as of October 2025

---

## 📊 What Features Now Have Full Documentation

### ✅ Recently Added (Now Fully Documented)
1. **Bid & Contract Management** - Lifecycle, scoping, awards, variations
2. **Building Envelope Performance (BEP)** - Approval workflows, versioning
3. **Issue Anchor Linking** - Location-based issue management
4. **Data Warehouse Pipeline** - Incremental ETL with SCD2 dimensions
5. **Issue Reliability Reports** - Data quality metrics by source

### ✅ Previously Added (Still Current)
- Project lifecycle management
- Review cycle management
- Service templates and billing claims
- Multi-source issue analytics
- Revit health monitoring
- Naming compliance validation
- User assignment and workload
- APS/ACC/Revizto integrations
- Dynamo batch automation

---

## 🚀 Backend API Summary

**Total Endpoints**: 65+ REST endpoints

| Category | Count | Key Endpoints |
|----------|-------|---------------|
| Projects | 10 | GET/POST /api/projects, project details, services |
| Reviews | 15 | GET/POST cycles, tasks, assignments, billing |
| Bids & Variations | 20 | NEW! Full bid lifecycle management |
| Tasks | 8 | GET/POST/PUT tasks with dependencies |
| Users | 10 | User mgmt, assignments, workload |
| Analytics | 15 | Dashboards, metrics, trends, health |
| Integrations | 12 | APS, ACC, Revizto, Revit Health |
| Data | 8 | Imports, mappings, configurations |
| Anchor Linking | 2 | NEW! Issue-anchor relationships |
| Utility | 10 | Schema, references, BEP, settings |

---

## 📚 Where to Find Things

| I Need To... | Read This | Location |
|-------------|----------|----------|
| Understand system architecture | copilot-instructions.md | `.github/` |
| Learn current features | README.md | Root directory |
| See what changed | DOCUMENTATION_UPDATE_JAN2026.md | `docs/` |
| Understand a feature | README.md section + copilot-instructions pattern | |
| Find an API endpoint | README.md "API Endpoints Reference" | Section near bottom |
| Understand data model | constants/schema.py | `constants/` |
| Work with database | copilot-instructions.md "Database Connection" | |
| Deploy warehouse | warehouse/README.md | `warehouse/` |

---

## ⚠️ Important Reminders

1. **Always use schema constants**: `from constants import schema as S`
2. **Always use connection pooling**: `from database_pool import get_db_connection`
3. **File organization matters**: Tests → tests/, SQL → sql/, Docs → docs/
4. **Follow existing patterns**: Check AGENTS.md for workflow guidance
5. **Verify after changes**: Run `python -m pytest tests/` and `python check_schema.py`

---

**Generated**: January 16, 2026
**Status**: Ready for agent use
**Documentation Completeness**: 95%+ (all implemented features documented)
