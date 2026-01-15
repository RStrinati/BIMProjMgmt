# AGENTS guidance for BIMProjMngmt

## 🚫 Core Model (Option A) - CRITICAL ARCHITECTURAL RULES

This system is built on the **Option A** core model. Deviation from this model is a critical bug.

### The Model
```
Project → Services → {Reviews, Items}
Project → Tasks
```

### What This Means (Examples)
- **Service Review**: A "Design Review" service has weekly review cycles (cadence) AND deliverables (items like "submittal review set")
- **Independent Peers**: Reviews and Items both attach to a service but do NOT depend on each other
- **Tasks are Separate**: "Coordinate HVAC ductwork" is a project task, not a service review or item
- **Import Rule**: ACC issues attach to Project + Service, optionally with Review/Item context. Unmapped is valid.

### Agent Rules You Must Follow

1. **Never conflate Items and Tasks**: Items = service offerings (deliverables); Tasks = project execution
2. **Preserve review/item independence**: A service can have reviews without items and items without reviews
3. **Link imports by priority**: Always project, prefer service, optionally review/item, unmapped is valid
4. **Enforce schema invariants**: Items require service_id, Reviews require service_id, Tasks require project_id
5. **If you do not understand the model, ask clarifying questions** before writing code

### Reference
- Full details: See [copilot-instructions.md](./.github/copilot-instructions.md) → **CRITICAL: Items vs Tasks**
- README visual guide: See [README.md](./README.md) → **Core Conceptual Model**

---

## Skills
- `skill-creator` (see `C:/Users/RicoStrinati/.codex/skills/.system/skill-creator/SKILL.md`): use only when extending Codex via new shared skills or updating existing ones.
- `skill-installer` (see `C:/Users/RicoStrinati/.codex/skills/.system/skill-installer/SKILL.md`): use when the task explicitly requires installing a curated skill or pulling one from another repo.

Mentioned skills only need to be activated when the user names them or when the request clearly matches the descriptions above. Do not invoke any other hidden skills unless the user requests them later.

## Access requirements
- Database credentials live in `config.py` under `class Config`. The defaults are:
  - `DB_DRIVER`: `ODBC Driver 17 for SQL Server`
  - `DB_SERVER`: `.\SQLEXPRESS`
  - `DB_USER`: `admin02`
  - `DB_PASSWORD`: `1234`
  - `PROJECT_MGMT_DB`: `ProjectManagement`
  - `WAREHOUSE_DB`: `ProjectManagement`
- Override these via environment variables (for example, `DB_SERVER` or `WAREHOUSE_DB`) when connecting from scripts, CLI tools, or migrations.

## Workflow reminders
- Prefer caching or refactoring slow queries before extending timeouts.
- When editing dashboards or metrics code, keep logging (`logger.info`, `logger.warning`) for performance tracing enabled so future diagnostics remain visible.
- Document where to find feeds and metrics.
- Check `logs/app.log` for general Flask activity and `logs/warehouse.log` for the query timings referenced by the warehouse metrics endpoint.
- Frontend events sent via `/api/logs/frontend` are written to `logs/frontend.log`; confirm the React client can reach `/logs/frontend` (see `frontend/src/api/client.ts`) before relying on those entries.
