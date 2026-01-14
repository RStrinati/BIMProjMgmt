# Warehouse Implementation Guide

This guide describes how to deploy and operate the analytics warehouse
framework introduced in `warehouse/`. It aligns with the roadmap for
connecting issues, projects, services, and review data into a consolidated
analytics layer.

## 1. Prerequisites

- **Databases**: Operational data lives in `ProjectManagement`. The warehouse
  objects will reside inside the same `ProjectManagement` database
  (default via `Config.WAREHOUSE_DB`). Ensure you have DDL rights in this database.
- **Connectivity**: Service account with read access to `ProjectManagement`
  tables/views and read/write access to the warehouse database.
- **Python environment**: Uses existing project dependencies (`pyodbc`,
  logging utilities). No additional packages required.

## 2. Database Bootstrapping

Run the SQL scripts in the following order against `ProjectManagement` (or whichever
database you configure as `WAREHOUSE_DB`):

1. `warehouse/sql/create_control_tables.sql` – control schema (`ctl`).
2. `warehouse/sql/staging/create_staging_tables.sql` – raw staging tables.
3. `warehouse/sql/dimensions/create_dimensions.sql` – SCD dimensions.
4. `warehouse/sql/facts/create_fact_tables.sql` – analytical fact tables.
5. `warehouse/sql/bridges/create_bridge_tables.sql` – many-to-many helpers.
6. `warehouse/sql/marts/create_mart_views.sql` – BI friendly views.
7. `warehouse/sql/create_load_procs.sql` – stored procedures orchestrating
   dimension/fact loads.

> Tip: add these scripts to source-controlled migration pipelines (e.g. Azure
> DevOps, Flyway) to ensure consistent environments.

## 3. Configuration

- By default the pipeline targets `ProjectManagement`. Set `WAREHOUSE_DB`
  environment variable if you need to use another database.
- Review `.env` (or environment) to confirm driver, server, and credentials
  for both source and warehouse connections.

## 4. ETL Orchestration

`warehouse/etl/pipeline.py` implements the orchestration sequence:

1. Record ETL run metadata in `ctl.etl_run`.
2. Incrementally load staging tables using high-water marks stored in
   `ctl.watermark`. Data sets currently covered:
   - Issues (`vw_ProjectManagement_AllIssues`)
   - Processed issues (analytics enrichments)
   - Projects, services, service reviews (core delivery data)
3. Execute dimension loader stored procedures (SCD Type-2 logic).
4. Execute fact loaders to populate issue snapshots, service monthly metrics,
   review cycles, and cross-project KPIs.
5. Run baseline data-quality checks (foreign key integrity, review date logic)
   and persist outcomes in `ctl.data_quality_result`.
6. Mark ETL run success/failure with optional error messaging.

### Running the pipeline

```bash
python -m warehouse.etl.pipeline
```

Schedule via task scheduler/cron with appropriate virtual environment
activation. Monitor `ctl.etl_run` for statuses and durations.

## 5. Extending the Model

- **Additional staging feeds**: Add new `load_staging_*` methods and DDL.
- **Review stages / schedules**: Expand staging to include `ReviewStages`,
  populate `dim.review_stage`, and extend fact loaders accordingly.
- **Issue-review bridges**: Enhance `warehouse.usp_load_bridges` to capture
  review windows, focus areas, and closure outcomes.
- **Financial metrics**: Refine `fact.service_monthly` calculations once
  detailed actuals are available (e.g. join billing tables).
- **Data quality**: Add new `DataQualityCheck` instances to the pipeline or
  pass custom checks at runtime.

## 6. Deployment & Governance

- Use migrations to manage schema evolution.
- Enforce role-based access: read-only for analysts (mart + dim/fact views),
  restricted write for ETL service account.
- Monitor ETL via `ctl.etl_run` (status, timestamps) and integrate with
  observability tooling as needed.
- Document metric definitions in the business glossary to maintain semantic
  alignment across dashboards.

## 7. Next Steps

- Populate `dim.review_stage` (currently placeholder) once staging extracts
  are available.
- Enhance fact loaders with full logic for review events and issue alignment
  windows (requires business rule sign-off).
- Optimise mart views and add incremental refresh policies in downstream BI.

This framework establishes the end-to-end pipeline from raw extracts to
analytics-ready marts, enabling the multi-dimensional dashboards requested.
