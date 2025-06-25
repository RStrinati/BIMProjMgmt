# Review Management Tab Design Review

This document summarizes how the current `Review Management` tab relates to the desired all‑in‑one BIM Coordination Review Management tool. It provides a high level comparison of requested features with existing functionality and highlights areas for future work.

## Requested Functionality
- **Modular UI** with projects, review cycles and reviewer assignments.
- Editable tables to manage review cycles and assignments.
- Project summary panels and optional Gantt view.
- Contract compliance tracking (BEP, fees, deliverables).

The proposed data model includes tables for `Projects`, `ReviewCycles`, `ReviewAssignments` and `ContractualLinks`.

## Current Implementation Overview
The repository already provides a Tkinter based interface under `ui/tab_review.py` and associated database helpers:
- Projects and review cycles are loaded from the database using helper functions in `database.py`.
- Review schedules are created via `submit_review_schedule` in `review_handler.py` and displayed in a table where reviewers can be assigned.
- A summary panel shows selected project metadata.
- A Dash based `gantt_chart.py` visualises review dates.

## Gaps and Potential Enhancements
- **Inline Editing:** The current task table supports assigning reviewers but does not allow editing dates directly. Integrating inline editing for Treeview rows would align with the requested editable table feature.
- **Contractual Data:** The database layer lacks the optional `ContractualLinks` table. Adding this table and exposing data through the UI would enable contract compliance tracking.
- **Additional Metadata:** Fields such as fee, platforms and license duration are captured when submitting a schedule but are not yet surfaced in a dedicated project sidebar.

## Next Steps
1. Extend the database schema with `ReviewAssignments` and `ContractualLinks` as outlined in the proposal.
2. Enhance `tab_review.py` to include inline editable cells for review dates and status, and to surface contractual information in the summary panel.
3. Integrate the existing Gantt chart launch button more tightly with selected project and cycle information.

