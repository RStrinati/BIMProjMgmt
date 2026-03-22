# IFC + IDS Validation

## Overview
This feature validates IFC models against IDS requirements using IfcOpenShell + IfcTester.
It lives in the **Data Imports** page under **IFC Health Check**.

## Backend
Endpoints (project scoped):
- `POST /api/projects/<project_id>/ifc-validation/run`
- `GET /api/projects/<project_id>/ifc-validation/runs`
- `GET /api/projects/<project_id>/ifc-validation/runs/<run_id>`
- `GET /api/projects/<project_id>/ifc-validation/runs/<run_id>/report`
- `GET /api/projects/<project_id>/ifc-validation/ids-tests`
- `POST /api/projects/<project_id>/ifc-validation/ids-tests`
- `PUT /api/projects/<project_id>/ifc-validation/ids-tests/<ids_test_id>`
- `DELETE /api/projects/<project_id>/ifc-validation/ids-tests/<ids_test_id>`

## Data Model
SQL tables (ProjectManagement):
- `IfcIdsTests`
- `IfcValidationRuns`
- `IfcValidationFailures`

## Dependencies
Python:
- `ifcopenshell`
- `ifctester`

## UI
Tabs:
- **Validation**: upload IFC + IDS and run validation
- **Run History**: review past runs and download HTML reports
- **IDS Tests**: manage saved IDS test files

## Notes
- IFC/IDS uploads are stored temporarily on disk during validation.
- HTML report content is stored with the run for export.
