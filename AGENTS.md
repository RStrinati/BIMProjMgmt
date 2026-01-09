# AGENTS guidance for BIMProjMngmt

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
