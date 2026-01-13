# Issue Metrics Reliability Plan

## Goals
- Make issue KPIs and trends consistent, reliable, and verifiable.
- Use a canonical reporting grain and stable issue key.
- Gate dashboards to show only successful imports.
- Add automated data-quality checks that block bad runs.

## Scope and context
- Sources: ACC and Revizto issue feeds.
- Current reporting surfaces: dashboard KPIs, charts, history, and issues table.
- Current SQL objects in use: `vw_ProjectManagement_AllIssues`, `vw_issues_expanded`, `fact.issue_snapshot`, `dim.issue`, and `mart.issue_charts_daily`.
- Reliability risks: row multiplication on joins, mixed time windows, and non-unique business keys.

## Current lineage (summary)
- Dashboard KPIs: UI -> `/api/dashboard/issues-kpis` -> `get_dashboard_issues_kpis()` -> `fact.issue_snapshot`, `dim.issue`, `acc_data_schema.dbo.vw_issues_expanded`.
- Dashboard charts: UI -> `/api/dashboard/issues-charts` -> `get_dashboard_issues_charts()` -> `mart.issue_charts_daily` (fallback to `fact.issue_snapshot` + `dim.issue` + ACC view).
- Issues history: UI -> `/api/dashboard/issues-history` -> `get_warehouse_issues_history()` -> `fact.issue_snapshot` + `dim.date` + `dim.issue`.
- Issues table: UI -> `/api/dashboard/issues-table` -> `get_dashboard_issues_table()` -> `fact.issue_snapshot` + `dim.issue` + ACC view.
- Overview: UI -> `/api/issues/overview` -> `get_all_projects_issues_overview()` -> `vw_ProjectManagement_AllIssues`.
- Project overview: UI -> `/api/projects/{id}/issues/overview` -> `get_project_combined_issues_overview()` -> `vw_ProjectManagement_AllIssues`.

## Canonical reporting model (Issue Reliability Layer)

### Issue key
- `issue_key` = (`source_system`, `source_issue_id`, `source_project_id`).
- Rationale: `source_issue_id` can be project-scoped (ACC display_id, Revizto issue_number), so adding `source_project_id` prevents cross-project collisions.

### Tables / views
1) `Issues_Current` (table or view)
- Grain: 1 row per `issue_key` (latest state).
- Fields (minimum):
  - `issue_key` (computed or persisted)
  - `source_system`, `source_issue_id`, `source_project_id`
  - `project_id` (PM project id)
  - `status_raw`, `status_normalized`
  - `priority_raw`, `priority_normalized`
  - `discipline_raw`, `discipline_normalized`
  - `assignee_user_key` (normalized user key only)
  - `created_at`, `updated_at`, `closed_at`
  - `location_root`, `location_building`, `location_level`
  - `is_deleted`, `project_mapped`
  - `import_run_id`, `snapshot_id`

2) `Issues_Snapshots` (table)
- Grain: 1 row per `issue_key` per snapshot/run.
- Fields (minimum):
  - `issue_key`
  - `snapshot_date`, `snapshot_id`, `import_run_id`
  - `status_normalized`, `is_open`, `is_closed`
  - `backlog_age_days`, `resolution_days`
  - `project_id`, `source_system`

3) `ImportRuns` (table)
- Grain: 1 row per import execution.
- Fields (minimum):
  - `import_run_id`, `source_system`, `run_type`
  - `started_at`, `completed_at`, `status`
  - `source_watermark`, `row_count`, `notes`

4) `DataQualityResults` (table)
- Grain: 1 row per check per import run.
- Fields (minimum):
  - `import_run_id`, `check_name`, `severity`, `passed`, `details`, `checked_at`

### Status normalization
- Normalize all raw statuses into canonical values.
- Use existing `issue_status_map` as the single source of truth.
- Disallow raw statuses without a mapping; fail the run if coverage is not 100%.

### ACC and Revizto combination
- Default: combine without dedup across systems. `issue_key` includes `source_system` so ACC and Revizto issues remain distinct.
- Optional: add an `IssueEquivalence` table only if cross-system dedup becomes required.

## KPI definitions (canonical)
- Total issues: `COUNT(DISTINCT issue_key)` from `Issues_Current`.
- Active/open issues: `COUNT(DISTINCT issue_key)` where `status_normalized` is in open set.
- Closed issues: `COUNT(DISTINCT issue_key)` where `status_normalized` is closed set.
- Over 30 days: `COUNT(DISTINCT issue_key)` where `status_normalized` is open and `DATEDIFF(day, created_at, as_of_date) > 30`.
- New issues trend: `Issues_Snapshots` or `Issues_Current` using `created_at`.
- Closed issues trend: `Issues_Snapshots` or `Issues_Current` using `closed_at`.
- Activity trend: based on `updated_at` or activity snapshots.
- Open-as-of-date trend: snapshot-based from `Issues_Snapshots` (recommended).

## Gating rules (dashboard safety)
- Dashboards must use only the latest successful import run.
- Rules:
  - `ImportRuns.status = 'success'` (or equivalent) is required.
  - If no successful run exists, dashboards return empty data with a warning.
  - API responses log `import_run_id` and `snapshot_id`.

## Data quality checks (must block dashboards)
Minimum checks executed post-import:
1) Uniqueness: `Issues_Current` has unique `issue_key`.
2) Join explosion: counts unchanged after joining approved 1:1 dims (project).
3) Orphans: `project_id` exists in Projects; `assignee_user_key` resolves when not null.
4) Status coverage: all raw statuses mapped to normalized values.
5) Time sanity: `closed_at >= created_at` when closed.

Failure behavior:
- Mark `ImportRuns.status = 'failed'`.
- Record failure in `DataQualityResults`.
- Dashboards ignore failed runs.

## Logging and observability
- Keep `logger.info`/`logger.warning` logs in warehouse queries.
- Log the `import_run_id` and `snapshot_id` in dashboard responses.
- Reference logs:
  - `logs/app.log` for Flask endpoints.
  - `logs/warehouse.log` for warehouse metrics timing.
  - `logs/frontend.log` for frontend telemetry.

## Migration and rollout
- Add tables in `sql/migrations/`.
- Populate `Issues_Current` and `Issues_Snapshots` from the existing warehouse `fact.issue_snapshot` and `dim.issue`.
- Update dashboard queries in `database.py` to use canonical layer and `COUNT(DISTINCT issue_key)`.
- Add tests to validate invariants and gating behavior.

## Risks and mitigations
- Risk: existing `issue_id` is not globally unique. Mitigation: include `source_project_id` in `issue_key`.
- Risk: status mapping gaps. Mitigation: enforce 100% mapping coverage and fail runs on gaps.
- Risk: ACC joins by display_id only. Mitigation: resolve ACC issues by key and avoid 1:N joins at the fact grain.
