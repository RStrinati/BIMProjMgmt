# Frontend Prototype Plan

This document outlines a pragmatic path to a React front end for BIM Project Management while preserving existing Python services.

## Information Architecture (IA)

- Projects
  - Overview, Details, BEP, Documents, Tasks, Parameters
- Reviews
  - Planning (timeline, stages, cycles)
  - Tracking (grid, status, folders, evidence)
  - Services (contract scope → review generation)
  - Kanban (To Plan, Scheduled, In Review, Issued, Actioned)
- Imports (ACC / Revit / IFC)
- Validation
- Issues / Coordination
- KPIs & Reports

## Prototype Milestones

1. Reviews: Planning & Tracking screens (MUI DataGrid + Date pickers)
2. Projects: List + detail split view
3. Kanban lane for review lifecycle
4. Optional: ACC viewer placeholder embed slot

## Validation Plan (30–45 min)

- Task 1: Select project and read review schedule overview
- Task 2: Add a stage with start/end and generate cycles
- Task 3: Change a review date and assign reviewer
- Task 4: Attach a folder path to a review and verify files render
- Task 5: Filter grid by status and cycle
- Task 6: Switch to Kanban and drag a review to Issued

Success criteria: completion time, error count, SUS score, top 3 frictions.

## Decision Matrix (Tkinter vs React)

- React: component density, real-time collab, browser access, ACC embed integration
- Tkinter: local utilities and quick admin operations, offline usage

Recommendation: keep Python backend services and run a 2–3 week React spike for Reviews module, with shared endpoints (/api/*).
