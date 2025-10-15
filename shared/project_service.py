"""Shared project service logic for both Tkinter and Flask layers.

This module centralises the project-related business rules that were
previously duplicated across the Tkinter UI and the Flask API.  The goal
is to make the same validation, default handling, and database access
available to the forthcoming React frontend without breaking the
existing desktop experience.

Functions exported here should only return plain Python primitives
(`dict`, `list`, etc.) so that callers from either environment can shape
responses or UI feedback however they need.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional

from constants import schema as S
from database import (
    get_project_details,
    get_project_folders,
    get_projects,
    get_projects_full,
    insert_project_full,
    update_project_record,
    get_db_connection,
)

PRIORITY_MAP = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
REVERSE_PRIORITY_MAP = {v: k for k, v in PRIORITY_MAP.items()}


class ProjectServiceError(Exception):
    """Base exception for project service failures."""


class ProjectValidationError(ProjectServiceError):
    """Raised when payload validation fails."""


class ProjectNotFoundError(ProjectServiceError):
    """Raised when a requested project cannot be found."""


@dataclass
class ProjectPayload:
    """Normalised payload used for insert/update operations."""

    name: str
    folder_path: str = ""
    ifc_folder_path: str = ""
    start_date: str = ""
    end_date: str = ""
    client_id: Optional[int] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    area: Optional[str] = None
    mw_capacity: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postcode: Optional[str] = None
    project_number: Optional[str] = None
    description: Optional[str] = None
    type_id: Optional[int] = None
    internal_lead: Optional[int] = None

    def to_db_payload(self) -> Dict[str, Any]:
        """Convert to a payload suitable for database helpers."""
        from database import get_db_connection

        default_start = datetime.now().strftime("%Y-%m-%d")
        default_end = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")

        # Handle dates: convert empty strings to None for SQL Server
        start_date_val = self.start_date.strip() if self.start_date else ""
        end_date_val = self.end_date.strip() if self.end_date else ""
        
        payload: Dict[str, Any] = {
            S.Projects.NAME: self.name,
            S.Projects.FOLDER_PATH: self.folder_path or "",
            S.Projects.IFC_FOLDER_PATH: self.ifc_folder_path or "",
            S.Projects.START_DATE: start_date_val if start_date_val else None,
            S.Projects.END_DATE: end_date_val if end_date_val else None,
        }

        if self.client_id:
            payload[S.Projects.CLIENT_ID] = self.client_id
        if self.status:
            payload[S.Projects.STATUS] = self.status
        if self.priority:
            payload[S.Projects.PRIORITY] = PRIORITY_MAP.get(self.priority, PRIORITY_MAP["Medium"])
        if self.area not in (None, ""):
            payload[S.Projects.AREA_HECTARES] = self.area
        if self.mw_capacity not in (None, ""):
            payload[S.Projects.MW_CAPACITY] = self.mw_capacity
        if self.address not in (None, ""):
            payload[S.Projects.ADDRESS] = self.address
        if self.city not in (None, ""):
            payload[S.Projects.CITY] = self.city
        if self.state not in (None, ""):
            payload[S.Projects.STATE] = self.state
        if self.postcode not in (None, ""):
            payload[S.Projects.POSTCODE] = self.postcode
        if self.project_number not in (None, ""):
            payload[S.Projects.CONTRACT_NUMBER] = self.project_number
        
        # Convert project_type name to type_id
        if self.type_id is not None:
            payload[S.Projects.TYPE_ID] = self.type_id
        if self.internal_lead is not None:
            payload[S.Projects.INTERNAL_LEAD] = self.internal_lead

        return payload


def _require_fields(payload: Dict[str, Any], required: Iterable[str]) -> None:
    missing = [field for field in required if not payload.get(field)]
    if missing:
        raise ProjectValidationError(f"Missing required fields: {', '.join(missing)}")


def _normalise_payload(raw_payload: Dict[str, Any]) -> ProjectPayload:
    _require_fields(raw_payload, ["name"])

    priority = raw_payload.get("priority")
    if priority and priority not in PRIORITY_MAP:
        raise ProjectValidationError(f"Unsupported priority '{priority}'")

    client_id = raw_payload.get("client_id")
    try:
        client_id_int = int(client_id) if client_id not in (None, "") else None
    except (TypeError, ValueError) as exc:
        raise ProjectValidationError("client_id must be numeric if provided") from exc

    # Safely handle dates that might be None
    start_date = raw_payload.get("start_date")
    end_date = raw_payload.get("end_date")
    
    start_date_str = start_date.strip() if start_date and isinstance(start_date, str) else ""
    end_date_str = end_date.strip() if end_date and isinstance(end_date, str) else ""

    type_id = raw_payload.get("type_id")
    project_type = raw_payload.get("project_type")
    
    # If type_id is not provided but project_type is, look up the type_id
    if not type_id and project_type:
        try:
            with get_db_connection("ProjectManagement") as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT {S.ProjectTypes.TYPE_ID} FROM {S.ProjectTypes.TABLE} WHERE {S.ProjectTypes.TYPE_NAME} = ?", (project_type,))
                row = cursor.fetchone()
                if row:
                    type_id = row[0]
        except Exception as e:
            # If lookup fails, ignore and continue
            pass
    
    try:
        type_id_int = int(type_id) if type_id not in (None, "") else None
    except (TypeError, ValueError) as exc:
        raise ProjectValidationError("type_id must be numeric if provided") from exc

    # Map all possible frontend keys to backend fields
    def safe_strip(val):
        if val is None:
            return ""
        if isinstance(val, str):
            return val.strip()
        return str(val).strip()

    return ProjectPayload(
        name=safe_strip(raw_payload.get("project_name") or raw_payload.get("name") or ""),
        folder_path=safe_strip(raw_payload.get("folder_path") or ""),
        ifc_folder_path=safe_strip(raw_payload.get("ifc_folder_path") or ""),
        start_date=start_date_str,
        end_date=end_date_str,
        client_id=client_id_int,
        status=raw_payload.get("status") or None,
        priority=priority,
        area=safe_strip(raw_payload.get("area") or raw_payload.get("area_m2") or "") or None,
        mw_capacity=safe_strip(raw_payload.get("mw_capacity") or raw_payload.get("mw_capacity_mw") or "") or None,
        address=safe_strip(raw_payload.get("address") or raw_payload.get("project_address") or "") or None,
        city=safe_strip(raw_payload.get("city") or raw_payload.get("project_city") or "") or None,
        state=safe_strip(raw_payload.get("state") or raw_payload.get("project_state") or "") or None,
        postcode=safe_strip(raw_payload.get("postcode") or raw_payload.get("project_postcode") or "") or None,
        project_number=safe_strip(raw_payload.get("project_number") or raw_payload.get("contract_number") or "") or None,
        description=safe_strip(raw_payload.get("description") or raw_payload.get("project_description") or "") or None,
        type_id=type_id_int,
        internal_lead=raw_payload.get("internal_lead"),
    )


def list_projects_basic() -> List[Dict[str, Any]]:
    """Return projects suitable for dropdowns."""

    results = []
    for project_id, name in get_projects() or []:
        results.append({"project_id": project_id, "name": name})
    return results


def list_projects_full() -> List[Dict[str, Any]]:
    """Return detailed project dictionaries with priority labels normalised."""

    projects = get_projects_full() or []
    for project in projects:
        priority_value = project.get(S.Projects.PRIORITY)
        if priority_value in REVERSE_PRIORITY_MAP:
            project["priority_label"] = REVERSE_PRIORITY_MAP[priority_value]
        elif isinstance(priority_value, str) and priority_value in PRIORITY_MAP:
            # Some queries already provide the label.
            project["priority_label"] = priority_value
        else:
            project["priority_label"] = "Medium"
    return projects


def get_project(project_id: int) -> Dict[str, Any]:
    """Fetch project details with folder paths."""

    details = get_project_details(project_id)
    if not details:
        raise ProjectNotFoundError(f"Project {project_id} not found")

    folder_path, ifc_folder_path = get_project_folders(project_id)
    details.update({
        "project_id": project_id,
        "folder_path": folder_path,
        "ifc_folder_path": ifc_folder_path,
        "priority_label": REVERSE_PRIORITY_MAP.get(details.get("priority"), details.get("priority")),
    })
    return details


def create_project(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create a project and return the normalised data used."""

    normalised = _normalise_payload(payload)
    success = insert_project_full(normalised.to_db_payload())
    if not success:
        raise ProjectServiceError("Database rejected project insert")
    return {"success": True}


def update_project(project_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing project."""

    normalised = _normalise_payload(payload)
    db_payload = normalised.to_db_payload()
    success = update_project_record(project_id, db_payload)
    if not success:
        raise ProjectServiceError("Database rejected project update")
    return {"success": True}

