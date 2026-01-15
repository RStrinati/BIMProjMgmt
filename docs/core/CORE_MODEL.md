# Core Model (Option A)

## Authoritative Hierarchy

```
Project
  ├── Services
  │   ├── Reviews (cadence-based, recurring cycles)
  │   └── Items (deliverables, one-off or bundled)
  └── Tasks (project execution, independent)
```

## Definitions

### Service
A bundled offering or scope area within a project. A service packages both **review cycles** and **deliverables** for a specific project function (e.g., "Design Review", "BIM Coordination").

### Review
A recurring cycle or cadence of project reviews under a service. Reviews define:
- Meeting/review schedule
- Participants and responsibilities
- Billing integration for service cycles

**Example**: "Weekly Design Review" (every Friday, 2-hour cycle)

### Item
A specific deliverable or offering within a service. Items are independent of review cycles and represent:
- Scope items bundled with a service
- One-off or recurring deliverables
- Service-level commitments

**Example**: "Submittal review set" (deliverable), "Monthly progress report" (deliverable)

### Task
A project-level execution unit, separate from services. Tasks represent:
- Work to be done on the project
- Coordination activities
- Tracking and accountability at the project level

**Example**: "Coordinate HVAC ductwork", "Prepare RFI response"

## Core Model Invariants

| Invariant | Meaning | Example |
|-----------|---------|---------|
| **Reviews require a Service** | Every Review must have `service_id` | "Weekly Design Review" belongs to Design Review service |
| **Items require a Service** | Every Item must have `service_id` | "Progress Report" deliverable belongs to Delivery service |
| **Tasks require a Project** | Every Task must have `project_id` | "Coordinate HVAC" belongs to Project, not Service |
| **Reviews ≠ Items** | Reviews and Items are independent peers | A service can have reviews without items |
| **Items ≠ Tasks** | Items (deliverables) are not Tasks (execution) | Do NOT create a Task for a Service Item |

## Explicit Statement

**Items are NOT Tasks.** Items are service-owned deliverables; Tasks are project-owned execution units.

**Reviews and Items are peers under Services.** Both attach to services, but do not depend on each other. A service can have reviews without items, and items without reviews.

## Linking Priority (for Imports)

When linking external data (ACC issues, Revizto, health checks) to the system:

```
1. project_id (ALWAYS REQUIRED)
   ↓
2. service_id (PRIMARY - use when scope is clear)
   ↓
3. review_id (OPTIONAL - context only)
   ↓
4. item_id (OPTIONAL - context only)
   ↓
5. UNMAPPED (VALID STATE - when mapping is undefined)
```

Unmapped imports are valid and expected. Do not force imports into the Task system.
