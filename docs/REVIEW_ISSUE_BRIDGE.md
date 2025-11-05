# Review-Issue Bridge: Linking Reviews and Issues

## Problem Statement
Previously, the warehouse had **no direct link** between review cycles and issues:
- **Reviews** (dim.review_cycle, fact.review_cycle) were tied to services and projects
- **Issues** (dim.issue, fact.issue_snapshot) were tied to projects
- They only met at the **project level**, making it impossible to answer:
  - "Which issues were opened/closed during a specific review cycle?"
  - "What was the issue activity around a review?"

## Solution Implemented

### 1. Bridge Table: `brg.review_issue`
**Location**: `warehouse/sql/bridges/create_review_issue_bridge.sql`

**Purpose**: Many-to-many bridge linking review cycles to issues based on temporal windows.

**Columns**:
- `review_cycle_sk`: FK to dim.review_cycle
- `issue_sk`: FK to dim.issue
- `relationship_type`: 
  - `'opened_during'`: issue created in the review window
  - `'closed_during'`: issue closed in the review window
  - `'opened_and_closed_during'`: both created and closed in window
  - `'active_during'`: issue was active (open) during the window

**Window logic**: ±14 days from the review's `planned_date`

### 2. Enhanced Fact Loader: `warehouse.usp_load_fact_review_cycle`
**Location**: `warehouse/sql/create_load_procs.sql`

**Changes**:
- Now computes `issue_count_window` and `issue_closed_window` metrics
- Uses a temp table `#review_issue_counts` to aggregate issues by review window
- Populates fact.review_cycle with actual issue counts instead of NULL

**Window logic**: Same ±14 day window around `planned_date_sk`

### 3. Bridge Loader: `warehouse.usp_load_bridges`
**Location**: `warehouse/sql/create_load_procs.sql`

**Changes**:
- Extended to populate `brg.review_issue` alongside existing `brg.issue_category`
- Links issues to reviews when created/closed dates fall within the review window
- Prevents duplicates via `NOT EXISTS` check

## Data Flow

```
Projects (dbo.Projects)
    ↓ seed_from_pm.sql
stg.projects → dim.project
    ↓
Services (dbo.ProjectServices)
    ↓ seed_from_pm.sql
stg.project_services → dim.service
    ↓
Reviews (dbo.ServiceReviews)
    ↓ seed_from_pm.sql
stg.service_reviews → dim.review_cycle → fact.review_cycle (with issue counts)
                              ↓
                       brg.review_issue ← dim.issue (from ACC issues)
                              ↑
Issues (ACC vw_issues_expanded_pm)
    ↓ seed_from_acc.sql
stg.issues → dim.issue → fact.issue_snapshot
```

## How to Use

### Query issues for a specific review cycle
```sql
SELECT 
    rc.review_cycle_sk,
    s.service_name,
    p.project_name,
    i.title AS issue_title,
    bri.relationship_type,
    i.status,
    i.priority
FROM brg.review_issue bri
JOIN dim.review_cycle rc ON bri.review_cycle_sk = rc.review_cycle_sk
JOIN dim.issue i ON bri.issue_sk = i.issue_sk
JOIN dim.service s ON rc.service_sk = s.service_sk
JOIN dim.project p ON s.project_sk = p.project_sk
WHERE rc.review_cycle_sk = <review_id>
ORDER BY bri.relationship_type, i.created_date_sk;
```

### Query reviews for a specific issue
```sql
SELECT 
    i.issue_bk,
    i.title,
    rc.cycle_no,
    s.service_name,
    d.date AS planned_review_date,
    bri.relationship_type
FROM brg.review_issue bri
JOIN dim.issue i ON bri.issue_sk = i.issue_sk
JOIN dim.review_cycle rc ON bri.review_cycle_sk = rc.review_cycle_sk
JOIN dim.service s ON rc.service_sk = s.service_sk
JOIN dim.date d ON rc.planned_date_sk = d.date_sk
WHERE i.issue_bk = '<issue_id>' AND i.source_system = 'ACC'
ORDER BY d.date;
```

### Mart views automatically benefit
- `mart.v_review_performance` now shows:
  - `issue_count_window`: count of issues created in review window
  - `issue_closed_window`: count of issues closed in review window
- No changes needed to the mart views; they already reference these columns

## Execution Order

1. Run seeds:
   - `warehouse/sql/staging/seed_from_pm.sql` (projects, services, reviews)
   - `warehouse/sql/staging/seed_from_acc.sql` (issues)

2. Recreate procs:
   - `warehouse/sql/bridges/create_review_issue_bridge.sql` (once, creates table)
   - `warehouse/sql/create_load_procs.sql` (recreates all procs with new logic)

3. Run full load:
   - `warehouse/sql/run_full_load.sql`
   - Dimensions load first
   - Facts load (including enhanced review_cycle with issue counts)
   - Bridges load (including new review-issue links)

## Notes

- Window is configurable: currently ±14 days; adjust `DATEADD(DAY, -14, ...)` and `DATEADD(DAY, 14, ...)` in both the fact loader and bridge loader if needed
- Bridge is idempotent: re-running `usp_load_bridges` won't create duplicates
- For incremental loads, consider truncating `brg.review_issue` and rebuilding, or adding batch/effective date filters
