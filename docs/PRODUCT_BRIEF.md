# Platform Product Brief (Partners)

## Purpose & Positioning
This platform is a unified project intelligence hub that bridges Autodesk Construction Cloud (ACC) and Revizto issue workflows. It acts as the missing orchestration layer between clash/CDE platforms and day‑to‑day BIM project delivery, creating a central source of truth for issues, users, services, and reviews across tools. It reduces manual Power BI exports and spreadsheet dependence while enabling consistent, portfolio‑level reporting for multi‑client teams. The UI is configurable and table‑centric so PMs control their workspace and can tailor views to their workflow. The product is purpose‑built for BIM management flow and reporting — it is not a CDE replacement, not a clash detection tool, and not a CMS, and it does not aim to replace model authoring or storage systems.

## Problem & Opportunity
Issue data is fragmented across ACC and Revizto, with no unified view of users, issues, and services. Teams currently rely on manual exports, mapping, and Power BI modeling to assemble project reports, and each project ends up with different dashboard styling and definitions. Both PMs and senior management struggle to track progress consistently, which drives weak forecasting and resource planning as the team scales. The opportunity is to standardize the data foundation and reporting layer across projects and clients, reducing manual effort while enabling consistent, branded, and decision‑ready insights.

## MVP Definition
**Phase 1 (MVP)** delivers a working, internal platform that unifies ACC and Revizto issues/users and aligns them to project services, reviews, and deliverables. The core UI already exists (projects overview, project workspace with subpages for services, deliverables, updates, issues, tasks, and quality, plus dashboards and import controls) and is functioning in draft form; the focus is refinement and reliability rather than greenfield build.

**In scope (Phase 1):**
- Unified issues and users table combining ACC and Revizto data
- Project/services/reviews/deliverables alignment for issue context
- Configurable project overview and project workspace pages
- Dashboard views mirroring current project analytics
- Import control page to manage cadence and manual imports
- Model register workflow for model publish compliance (ACC/Aconex)
- Model health checks (warnings, coordinates, grids, levels) against a master control file

**Non‑negotiables:**
- ACC Issues + Revizto Issues
- User/project mapping across both platforms

**Constraints and known gaps (Phase 1):**
- ACC APS integration is limited to hubs where the APS app is installed; manual ACC exports remain required
- Revizto data is extracting reliably but has gaps vs ACC in available fields; unification/matching needs refinement
- Unified issues/users tables need an auditability workflow
- Access control, security hardening, and hosting are not yet addressed (currently local)
- Model register currently relies on manual model name entry and ACC desktop connector signals

**Out of scope for Phase 1:** 3D/2D viewer, asset management, planner integration, Cupix/OpenSpace

## Core Workflow
1. Import data on a controlled cadence: Revizto automated; ACC via manual exports where APS access is limited.  
2. Normalize and unify issues and users into a single table.  
3. Resolve aliases and mappings (project names, users, disciplines, zones/levels) to enforce consistency.  
4. Align issues to project services, reviews, and deliverables for contextual tracking.  
5. PMs configure table‑centric project views to match their workflow.  
6. Project teams manage issues, updates, tasks, and quality inside the workspace.  
7. Project dashboards provide project‑specific visibility; a company dashboard aggregates cross‑project reporting with filters.  
8. Model register tracks publish compliance, and model health flags coordinate/grid/level misalignment.  

## Milestones
**Phase A — Unified Tables + Auditability (Foundation)**
- Consolidate ACC + Revizto issues/users into unified tables
- Implement auditability for issue/user mappings and changes
- Establish consistent alias matching (projects, users, disciplines, zones/levels)

**Phase B — Automation & API Expansion**
- Improve ACC automation (APS coverage where possible)
- Expand Revizto extraction capability and field parity
- Reduce manual effort in data refresh cycles

**Phase C — Adoption & Operational Readiness**
- UI/graphics refresh as a dedicated workflow
- Pilot with live project teams and iterate based on usage
- Confirm productive, repeatable use across multiple projects

## Future Phases
- 3D/2D interface to align issues to model and drawings
- Asset management and client asset data capture
- Project program/schedule integration
- Cupix/OpenSpace capture alignment
- Advanced issue analytics and cross‑project business intelligence
- Model compliance roll‑ups in dashboards (portfolio and project)

## Partner Fit & Next Steps
We are seeking technical partners who can help close gaps across backend integrations and frontend experience. This likely requires multiple partners with complementary strengths (API integration, data engineering, and UI/UX refinement).

**Next steps:**
- Identify partners with ACC/APS and Revizto API experience to expand automation coverage
- Engage frontend/UX support to refine the workspace and dashboard experience
- Align on a joint roadmap for Phase 1 completion and Phase 2 expansion
