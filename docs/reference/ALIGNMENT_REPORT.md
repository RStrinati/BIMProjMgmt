# Cross-DB Alignment Review (ProjectManagement facts/marts vs acc_data_schema, RevitHealthCheckDB, ReviztoData)

Date: 2025-11-05
Scope: Review alignment of the ProjectManagement warehouse (dim/fact/mart) and OLTP tables with external data sources/databases: acc_data_schema (ACC), RevitHealthCheckDB (Revit health), and ReviztoData (Revizto). Focus on naming, keys, column coverage, and dependency integrity.

## Summary

Overall modeling is solid: the warehouse lives in ProjectManagement with clear schemas (stg, dim, fact, brg, mart). Integration points with ACC and Revit are present and mostly well thought out. Key gaps are missing helper objects in ProjectManagement (vw_dim_projects, project_aliases) and optimistic joins in Revit views to non-existent tables (clients, project_types, sectors). Revizto naming is inconsistent (ReviztoData vs rEVIZTOdATA). Addressing these will make facts/marts fully consumable and resilient.

## Inventory and Interfaces

- ProjectManagement (warehouse/OLTP)
  - Schemas: stg, dim, fact, brg, mart, dbo
  - Dimensions: dim.date, dim.project, dim.client, dim.project_type, dim.issue, dim.user, dim.service, dim.review_cycle, dim.review_stage
  - Facts: fact.issue_snapshot, fact.issue_activity, fact.service_monthly, fact.review_cycle, fact.review_event, fact.project_kpi_monthly
  - Bridges: brg.issue_category, brg.review_issue, brg.service_stage
  - Marts: mart.v_project_overview, mart.v_issue_trends, mart.v_review_performance
  - Staging: stg.issues, stg.processed_issues, stg.projects, stg.clients, stg.project_types, stg.project_services, stg.service_reviews, stg.review_schedule_events, stg.issue_categories
  - OLTP: Projects, ProjectServices, ServiceReviews, BillingClaims/Lines, ServiceDeliverables, tblControlModels, etc.

- acc_data_schema (source)
  - Core view: dbo.vw_issues_expanded (ACC issues unified + custom attributes)
  - Optional: dbo.vw_issues_expanded_pm (ACC issues with ProjectManagement mapping via vw_dim_projects + project_aliases)

- RevitHealthCheckDB (source)
  - Cross-DB view: dbo.vw_RevitHealthWarehouse_CrossDB (joins to ProjectManagement projects + tblControlModels)
  - Enhanced context views: vw_RevitHealth_{Grids,Levels,Coordinates}WithProjects; vw_RevitHealth_ProjectSummary; vw_RevitHealth_UnmappedFiles

- ReviztoData (source)
  - Consumed via view: dbo.vw_ReviztoProjectIssues_Deconstructed (referenced in tools)

## Alignment Findings

1) ACC → Warehouse (Issues)
- Good
  - vw_issues_expanded exposes: issue_id/display_id, status, dates, assignee/company/role, location, custom attributes (Priority, Phase, Location, …), and pm_project_id when using the _pm variant.
  - stg.issues schema matches the typical fields required to build dim.issue and fact.issue_snapshot.
  - Processed issue analytics (ProjectManagement.ProcessedIssues) aligns with stg.processed_issues structure (urgency/complexity/sentiment, categorization fields).
- Gaps
  - ProjectMapping requires ProjectManagement.dbo.vw_dim_projects and dbo.project_aliases. These are not present in repo SQL. Without them, acc_data_schema.dbo.vw_issues_expanded_pm cannot resolve pm_project_id.
  - No scripted ETL (INSERT…SELECT) from acc_data_schema.dbo.vw_issues_expanded into ProjectManagement.stg.issues; assumed to exist externally.
- Recommendation
  - Add helper view in ProjectManagement: vw_dim_projects (select current projects from dim.project or dbo.Projects).
  - Add table dbo.project_aliases with pm_project_id and alias_name columns.
  - Provide a simple ETL proc to populate stg.issues from acc_data_schema.dbo.vw_issues_expanded (or _pm when available).

2) RevitHealthCheckDB → Warehouse (Revit model health)
- Good
  - vw_RevitHealthWarehouse_CrossDB models a wide analytic surface and uses ProjectManagement.dbo.tblControlModels to enrich with control metadata.
  - Wrapper views (vw_Rvt*) standardize base qry_* names; enhanced context views join to the cross-db warehouse view.
- Gaps
  - Cross-db joins assume ProjectManagement tables: projects, clients, project_types, sectors. Only dbo.Projects exists in repo (minimal columns). No SQL for clients/project_types/sectors tables in ProjectManagement.
  - Prefer joining the warehouse dim tables (dim.project, dim.client, dim.project_type) rather than OLTP placeholders for analytics.
- Recommendation
  - Either (A) create OLTP lookup tables (clients, project_types, sectors) to satisfy joins, or (B) change the Revit view to join dim tables via a small compatibility view in ProjectManagement (e.g., vw_projects_compat exposing expected columns from dim.project and related dims).
  - Keep tblControlModels (exists with bootstrap script) – OK.

3) ReviztoData → Warehouse (Issues)
- Good
  - Tools reference ReviztoData.dbo.vw_ReviztoProjectIssues_Deconstructed for source ingestion.
- Gaps
  - Inconsistent naming in text (rEVIZTOdATA vs ReviztoData). SQL Server is case-insensitive for object names by default, but consistency avoids confusion.
  - No scripted ETL from ReviztoData into stg.issues.
- Recommendation
  - Standardize name to ReviztoData in scripts and docs.
  - Add an ETL proc to insert Revizto issues into stg.issues with source_system='Revizto'.

4) Warehouse internals (facts/marts) vs sources
- Good
  - dim/fact/mart schemas and SCD2 loaders are consistent and use hash-based change detection; surrogate key strategy is sound.
  - mart views only depend on dim/fact/bridge within ProjectManagement – no cross-db dependency at the mart layer.
- Gaps
  - mart.v_issue_trends references brg.issue_category with category_role='discipline'; ensure bridge load procedure covers all category roles if needed (only 'discipline' implemented currently).
  - dim.review_stage loader is a placeholder; add staging + loader when stage data is available.

## Quick Gap Matrix

- ProjectManagement helpers
  - vw_dim_projects: MISSING → required by ACC mapping
  - dbo.project_aliases: MISSING → required by ACC mapping
  - dbo.clients, dbo.project_types, dbo.sectors: MISSING → referenced by Revit cross-db view
- ETL into stg.*
  - From ACC issues view: NOT SCRIPTED
  - From Revizto view: NOT SCRIPTED
  - From OLTP services/reviews: NOT SCRIPTED (but stg tables exist)

## Proposed Minimal Fixes (Safe to add now)

1) Add vw_dim_projects in ProjectManagement
- Definition: map dim.project current rows to a flat view exposing pm_project_id and project_name (and optional status/type/sector).

2) Add dbo.project_aliases table in ProjectManagement
- Columns: pm_project_id INT NOT NULL FK to projects (or dim.project.project_bk), alias_name NVARCHAR(510) NOT NULL; unique(pm_project_id, alias_name).

3) Prepare compatibility view for Revit joins (optional, if you keep current Revit view)
- vw_projects_compat: expose columns project_id, project_name, status, client_id, type_id, sector_id by translating from dim.project and related dims.

4) Standardize Revizto DB name in docs/scripts to ReviztoData

## Suggested SQL Snippets

- vw_dim_projects (ProjectManagement):
  CREATE OR ALTER VIEW dbo.vw_dim_projects AS
  SELECT
      p.project_bk     AS pm_project_id,
      p.project_name   AS project_name,
      p.status,
      p.priority
  FROM dim.project p
  WHERE p.current_flag = 1;

- project_aliases:
  CREATE TABLE dbo.project_aliases (
      pm_project_id INT NOT NULL,
      alias_name    NVARCHAR(510) NOT NULL,
      created_at    DATETIME2 DEFAULT SYSDATETIME(),
      CONSTRAINT pk_project_aliases PRIMARY KEY (pm_project_id, alias_name)
  );

## Risk/Impact

- Low risk: adding helper view/table does not affect existing facts/marts and unblocks acc_data_schema.vw_issues_expanded_pm mapping.
- Revit view adjustments: if you switch to dim.* joins via a compat view, ensure permissions are granted across DBs.

## Next Steps

- Create the two helper SQL files and run them on ProjectManagement.
- Optionally add simple ETL procs to populate stg.* from ACC/Revizto.
- Validate: run warehouse.usp_load_* procs end-to-end and check marts.
- Align docs: use consistent ReviztoData DB name.
