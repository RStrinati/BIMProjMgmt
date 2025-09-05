from typing import List, Dict, Optional, Tuple
import json
from datetime import datetime

from .dao import (
    get_connection,
    ensure_schema,
    get_or_create_library,
    seed_library_from_json,
    fetch_library_sections,
    instantiate_document as dao_instantiate_document,
    list_project_document_sections,
    list_project_clauses,
    insert_assignment,
    create_revision,
    add_published_file,
    approve_revision,
)


def ensure_ready(db_name: str = "ProjectManagement"):
    conn = get_connection(db_name)
    if not conn:
        return None
    ensure_schema(conn)
    return conn


def import_library_seed(conn, document_type: str, seed_data: Dict, template_name: str = "WIP", version: str = "1.0", jurisdiction: Optional[str] = None) -> int:
    lib_id = get_or_create_library(conn, document_type, template_name, version, jurisdiction)
    seed_library_from_json(conn, lib_id, seed_data)
    return lib_id


def list_library(conn, document_type: str, filters: Optional[Dict] = None) -> List[Dict]:
    return fetch_library_sections(conn, document_type, filters)


def instantiate_document(conn, project_id: int, library_id: int, title: str, version: str,
                         document_type: str, include_optional: bool = True,
                         selected_section_ids: Optional[List[int]] = None) -> int:
    return dao_instantiate_document(conn, project_id, library_id, title, version, document_type,
                                    include_optional, selected_section_ids)


def assign_clause(conn, project_clause_id: int, discipline: str, owner: str, due_date: Optional[str],
                  evidence_type: str, check_type: str, check_ref: Optional[str], params_json: Optional[str]) -> int:
    # Basic validation
    if owner and "@" not in owner and (not discipline):
        # Allow free-form owner names but encourage email later
        pass
    if check_type == 'SQL_VIEW' and not check_ref:
        raise ValueError("check_ref (view name) is required for SQL_VIEW checks")
    return insert_assignment(conn, project_clause_id, discipline, owner, due_date, evidence_type, check_type, check_ref, params_json)


def get_document_outline(conn, project_document_id: int) -> Tuple[List[Dict], List[Dict]]:
    sections = list_project_document_sections(conn, project_document_id)
    clauses = list_project_clauses(conn, project_document_id)
    return sections, clauses


def publish_document(conn, project_document_id: int, change_note: str, formats: Tuple[str, ...] = ("DOCX",), created_by: Optional[str] = None) -> Dict:
    rev_id = create_revision(conn, project_document_id, change_note, created_by)
    files = []
    from .export import render_docx
    docx_path = None
    if "DOCX" in formats:
        try:
            docx_path = render_docx(conn, project_document_id)
        except Exception:
            docx_path = None
        if docx_path:
            add_published_file(conn, rev_id, docx_path, "DOCX")
            files.append(docx_path)
    return {"revision_id": rev_id, "files": files}


def approve_document(conn, project_document_id: int, approved_by: str) -> bool:
    return approve_revision(conn, project_document_id, approved_by)

