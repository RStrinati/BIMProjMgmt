# Project Management Warehouse Framework

This package implements the analytics warehouse scaffolding requested for the
project issues/services/reviews dashboard initiative. It provides:

- **SQL DDL** for staging, dimension, fact, bridge, mart, and control tables.
- **Incremental ETL orchestration** via `warehouse/etl/pipeline.py` that
  extracts from the operational ProjectManagement database, loads staging,
  executes dimension/fact stored procedures, and records run metadata.
- **Stored procedures** under the `warehouse` schema encapsulating SCD2
  logic and fact population.
- **Data quality hooks** recording validation results inside
  `ctl.data_quality_result`.

## Layout

```
warehouse/
├── README.md
├── __init__.py
├── etl/
│   ├── __init__.py
│   └── pipeline.py
└── sql/
    ├── create_control_tables.sql
    ├── create_load_procs.sql
    ├── bridges/
    │   └── create_bridge_tables.sql
    ├── dimensions/
    │   └── create_dimensions.sql
    ├── facts/
    │   └── create_fact_tables.sql
    ├── marts/
    │   └── create_mart_views.sql
    └── staging/
        └── create_staging_tables.sql
```

## Initialisation Workflow

1. **Confirm target database** (defaults to `ProjectManagement`
   via `Config.WAREHOUSE_DB`). No new database is required—schemas will be created
   inside the existing `ProjectManagement` database.
2. Execute SQL DDL scripts in this order:
   1. `sql/create_control_tables.sql`
   2. `sql/staging/create_staging_tables.sql`
   3. `sql/dimensions/create_dimensions.sql`
   4. `sql/facts/create_fact_tables.sql`
   5. `sql/bridges/create_bridge_tables.sql`
   6. `sql/marts/create_mart_views.sql`
   7. `sql/create_load_procs.sql`
3. Configure security (service account with rights on both source DB and `ProjectManagement`
   for schema/table creation).
4. No database renaming is required—the framework will create its schemas
   (`ctl`, `stg`, `dim`, `fact`, `brg`, `mart`, `warehouse`) inside `ProjectManagement`.
4. Run the Python pipeline:

```bash
python -m warehouse.etl.pipeline
```

The pipeline performs:

| Stage | Description |
|-------|-------------|
| Staging Load | Pulls issues, processed analytics, projects, services, and service reviews incrementally from the operational database using watermarks. |
| Dimension Load | Calls stored procedures implementing SCD Type-2 logic for clients, project types, projects, issues, users, services, and review cycles. |
| Fact Load | Populates daily issue snapshots, monthly service metrics, review cycle facts, and project KPIs. |
| Data Quality | Executes configurable validation queries, storing results in `ctl.data_quality_result`. |

All runs are logged in `ctl.etl_run`, supporting observability and retries.

## Extending the Framework

- Implement high-fidelity logic inside stored procedures as source data
  matures (e.g. populate review stages, enrich review events).
- Add new staging extracts by mirroring the pattern in `pipeline.py`
  (`load_staging_*` methods) and corresponding SCD2 loaders.
- Enhance data-quality rules by supplying custom `DataQualityCheck` objects
  to `WarehousePipeline.run_data_quality_checks`.
- Layer additional marts by appending SQL views inside `sql/marts`.

## Configuration

`Config.WAREHOUSE_DB` controls the target database. Set environment variables
if using a non-default name:

```
export WAREHOUSE_DB=ProdWarehouse
```

Logging level follows `Config.LOG_LEVEL`. Adjust in `.env` or environment.

## Roadmap Alignment

The implementation covers the agreed roadmap:

1. **Architecture scaffolding** (staging + star schema + control tables).
2. **Incremental ETL pipeline** implemented in Python.
3. **Stored procedures** encapsulate dimensional/fact logic for transparency.
4. **Data quality + auditing** ensures reliability and observability.
5. **Analytic marts/views** deliver ready-to-use datasets for dashboards.

Future work: populate review stage DIM/FACT with richer schedule feeds,
extend issue-review bridges, and optimise fact calculations for performance.
