import copy
import json
import logging
import os
import re
import sys
import subprocess
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal

# Add parent directory to path FIRST so we can import config and database
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from flask import Flask, jsonify, request
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS

from config import (
    ACC_SERVICE_TOKEN,
    ACC_SERVICE_URL,
    APS_AUTH_LOGIN_PATH,
    APS_AUTH_SERVICE_URL,
    REVIZTO_SERVICE_TOKEN,
    REVIZTO_SERVICE_URL,
)

from database import (  # noqa: E402
    add_bookmark,
    create_client,
    create_project_service,
    create_review_cycle,
    create_service_review,
    create_service_template,
    delete_bookmark,
    delete_client,
    delete_project,
    delete_project_service,
    delete_review_cycle,
    delete_service_review,
    delete_service_template,
    get_acc_folder_path,
    get_acc_import_logs,
    get_all_projects_issues_overview,
    get_bep_matrix,
    get_contractual_links,
    get_control_models,
    get_cycle_ids,
    get_db_connection,
    get_last_revizto_extraction_run,
    get_project_bookmarks,
    get_project_combined_issues_overview,
    get_project_details,
    get_project_folders,
    get_project_health_files,
    get_projects_full,
    get_client_by_id,
    get_clients_detailed,
    get_project_services,
    get_reference_options,
    get_review_cycle_tasks,
    get_review_cycles,
    get_review_summary,
    get_review_tasks,
    get_revizto_extraction_runs,
    complete_revizto_extraction_run,
    get_service_reviews,
    get_service_review_billing,
    get_service_templates,
    get_users_list,
    fetch_tasks_notes_view,
    insert_task_notes_record,
    update_task_notes_record,
    archive_task_record,
    delete_task_record,
    toggle_task_item_completion,
    insert_files_into_tblACCDocs,
    log_acc_import,
    save_acc_folder_path,
    start_revizto_extraction_run,
    update_bookmark,
    update_project_service,
    update_review_cycle,
    update_review_cycle_task,
    update_review_task_assignee,
    update_service_review,
    update_service_template,
    set_control_models,
    upsert_bep_section,
    update_bep_status,
    update_project_details,
    update_project_folders,
    update_client,
)
from shared.project_service import (  # noqa: E402
    ProjectServiceError,
    ProjectValidationError,
    create_project,
    list_projects_full,
    invalidate_projects_cache,
    update_project,
)
from constants import schema as S  # noqa: E402
from review_validation import ValidationError, validate_template  # noqa: E402
from review_management_service import ReviewManagementService  # noqa: E402
from services.project_alias_service import ProjectAliasManager  # noqa: E402


# --- Revizto utility helpers ---

def _find_revizto_exporter():
    """Locate the Revizto exporter executable and return (path, searched_paths)."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    possible_paths = [
        # New packaged locations (preferred)
        os.path.join(project_root, "services", "revizto-dotnet", "publish", "ReviztoDataExporter.exe"),
        os.path.join(project_root, "services", "revizto-dotnet", "bin", "Debug", "net9.0-windows", "win-x64", "ReviztoDataExporter.exe"),
        # Legacy/tooling fallback
        os.path.join(project_root, "tools", "ReviztoDataExporter.exe"),
        # Standard Windows installs
        r"C:\Program Files\Revizto\DataExporter\ReviztoDataExporter.exe",
        r"C:\Program Files (x86)\Revizto\DataExporter\ReviztoDataExporter.exe",
        r"C:\Revizto\DataExporter\ReviztoDataExporter.exe",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path, possible_paths
    return None, possible_paths


def _run_revizto_cli(exe_path, cli_args, timeout=900):
    """Run the Revizto exporter in CLI mode and capture parsed JSON plus raw output."""
    try:
        command = [exe_path] + cli_args
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(exe_path),
            timeout=timeout,
        )

        parsed = None
        parse_error = None
        stdout = (completed.stdout or "").strip()
        if stdout:
            # Try to parse the last JSON-looking line first to tolerate banner text
            for line in reversed(stdout.splitlines()):
                stripped = line.strip()
                if stripped.startswith("{") and stripped.endswith("}"):
                    try:
                        parsed = json.loads(stripped)
                        break
                    except Exception:
                        continue
            if parsed is None:
                try:
                    parsed = json.loads(stdout)
                except Exception as exc:  # noqa: BLE001 - need to surface parse failures
                    parse_error = str(exc)

        return {
            "command": command,
            "returncode": completed.returncode,
            "stdout": stdout,
            "stderr": (completed.stderr or "").strip(),
            "parsed": parsed,
            "parse_error": parse_error,
        }
    except Exception as exc:  # noqa: BLE001 - capture and bubble up unexpected errors
        logging.exception("Error running Revizto CLI")
        return {
            "command": cli_args,
            "returncode": -1,
            "stdout": "",
            "stderr": str(exc),
            "parsed": None,
            "parse_error": str(exc),
        }


def _extract_project_payload(body):
    """Extract and normalize project payload from request body."""
    return body


class CustomJSONProvider(DefaultJSONProvider):
    """Custom JSON provider to handle date, datetime, and Decimal objects."""
    
    def default(self, obj):
        if isinstance(obj, ValidationError):
            return {
                'field': obj.field,
                'message': obj.message,
                'value': obj.value,
            }
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
TEMPLATE_FILE_PATH = Path(__file__).resolve().parent.parent / "templates" / "service_templates.json"
app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
app.json = CustomJSONProvider(app)

CONTROL_MODEL_TARGETS = ('naming', 'coordinates', 'levels')


def _serialize_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time()).isoformat()
    return str(value)


def _normalise_validation_targets(targets):
    if not targets:
        return list(CONTROL_MODEL_TARGETS)
    seen = []
    for target in targets:
        value = str(target).strip().lower()
        if value in CONTROL_MODEL_TARGETS and value not in seen:
            seen.append(value)
    return seen or list(CONTROL_MODEL_TARGETS)


def _derive_zone_code(file_name):
    if not file_name:
        return None
    cleaned = str(file_name).strip()
    cleaned = re.sub(r'\[.*?\]$', '', cleaned)
    cleaned = re.sub(r'\.rvt$', '', cleaned, flags=re.IGNORECASE)
    parts = [part for part in re.split(r'[-_]', cleaned) if part]
    if len(parts) >= 3:
        return parts[2].upper()
    return None


def _build_control_model_configuration(project_id: int) -> dict:
    """Assemble control model configuration payload for API responses."""
    raw_models = get_control_models(project_id)
    available_models = get_project_health_files(project_id)

    control_models = []
    active_models = []
    primary_name = None

    for raw in raw_models:
        metadata_source = dict(raw.get('metadata') or {})
        validation_targets = _normalise_validation_targets(metadata_source.get('validation_targets'))
        volume_label = metadata_source.get('volume_label') or None
        notes = metadata_source.get('notes') or None
        zone_code = metadata_source.get('zone_code') or _derive_zone_code(raw.get('control_file_name'))
        is_primary = bool(metadata_source.get('is_primary'))

        metadata = {
            'validation_targets': validation_targets,
            'is_primary': bool(is_primary),
        }
        if volume_label:
            metadata['volume_label'] = volume_label
        if notes:
            metadata['notes'] = notes
        if zone_code:
            metadata['zone_code'] = str(zone_code).upper()

        control_entry = {
            'id': raw.get('id'),
            'file_name': raw.get('control_file_name'),
            'is_active': bool(raw.get('is_active')),
            'metadata': metadata,
            'created_at': _serialize_datetime(raw.get('created_at')),
            'updated_at': _serialize_datetime(raw.get('updated_at')),
        }
        control_models.append(control_entry)

        if control_entry['is_active']:
            active_models.append(control_entry)
            if metadata.get('is_primary') and not primary_name:
                primary_name = control_entry['file_name']

    if active_models and primary_name is None:
        primary_name = active_models[0]['file_name']
        active_models[0]['metadata']['is_primary'] = True

    readiness = {
        target: any(target in (entry['metadata'].get('validation_targets') or []) for entry in active_models)
        for target in CONTROL_MODEL_TARGETS
    }

    issues = []
    if not active_models:
        issues.append("No control models have been configured for this project.")
    else:
        for target, ready in readiness.items():
            if not ready:
                issues.append(f"{target.capitalize()} validation does not have an assigned control model.")

    validation_summary = {
        'naming_ready': readiness['naming'],
        'coordinates_ready': readiness['coordinates'],
        'levels_ready': readiness['levels'],
        'multi_volume_ready': len(active_models) > 1,
        'active_control_count': len(active_models),
        'issues': issues,
    }

    mode = 'none'
    if len(active_models) == 1:
        mode = 'single'
    elif len(active_models) > 1:
        mode = 'multi'

    return {
        'project_id': project_id,
        'available_models': available_models,
        'control_models': control_models,
        'primary_control_model': primary_name,
        'validation_summary': validation_summary,
        'mode': mode,
        'validation_targets': list(CONTROL_MODEL_TARGETS),
    }
CORS(app)


def _extract_project_payload(body):
    """Normalise incoming JSON into a payload for the project service."""
    
    # Handle dates - convert empty strings to None, and extract date part from ISO strings
    def normalize_date(date_value):
        if not date_value or date_value == '':
            return None
        if isinstance(date_value, str):
            # If it's an ISO datetime string, extract just the date part
            if 'T' in date_value:
                return date_value.split('T')[0]
            return date_value
        return None
    
    start_date = normalize_date(body.get('start_date'))
    end_date = normalize_date(body.get('end_date'))

    return {
        'name': body.get('project_name') or body.get('name'),
        'project_number': body.get('project_number'),
        'client_id': body.get('client_id'),
        'type_id': body.get('type_id'),
        'area': body.get('area') or body.get('area_m2') or body.get('area_hectares'),
        'mw_capacity': body.get('mw_capacity'),
        'status': body.get('status'),
        'priority': body.get('priority') or body.get('priority_label'),
        'start_date': start_date,
        'end_date': end_date,
        'address': body.get('address'),
        'city': body.get('city'),
        'state': body.get('state'),
        'postcode': body.get('postcode'),
        'folder_path': body.get('folder_path'),
        'ifc_folder_path': body.get('ifc_folder_path'),
        'description': body.get('description'),
        'internal_lead': body.get('internal_lead'),
        'naming_convention': body.get('naming_convention'),
    }


def _parse_int(value):
    try:
        if value in (None, '', 'null'):
            return None
        return int(value)
    except (ValueError, TypeError):
        return None


def _parse_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {'1', 'true', 'yes', 'y'}


def _clean_string(value, allow_empty=False):
    if not isinstance(value, str):
        return value
    cleaned = value.strip()
    if allow_empty:
        return cleaned
    return cleaned or None


def _extract_task_payload(body):
    """Normalise task payloads for create/update handlers."""
    payload = {}
    if not isinstance(body, dict):
        return payload

    if 'task_name' in body or 'taskName' in body or 'name' in body:
        name = body.get('task_name')
        if name is None and 'taskName' in body:
            name = body.get('taskName')
        if name is None and 'name' in body:
            name = body.get('name')
        payload[S.Tasks.TASK_NAME] = _clean_string(name)

    if 'project_id' in body or 'projectId' in body:
        project_id = body.get('project_id')
        if project_id is None and 'projectId' in body:
            project_id = body.get('projectId')
        payload[S.Tasks.PROJECT_ID] = _parse_int(project_id)

    if 'cycle_id' in body or 'cycleId' in body:
        cycle_id = body.get('cycle_id')
        if cycle_id is None and 'cycleId' in body:
            cycle_id = body.get('cycleId')
        payload[S.Tasks.CYCLE_ID] = _parse_int(cycle_id)

    if 'task_date' in body or 'taskDate' in body:
        task_date = body.get('task_date')
        if task_date is None and 'taskDate' in body:
            task_date = body.get('taskDate')
        payload[S.Tasks.TASK_DATE] = _clean_string(task_date)

    if 'start_date' in body or 'startDate' in body:
        start_date = body.get('start_date')
        if start_date is None and 'startDate' in body:
            start_date = body.get('startDate')
        payload[S.Tasks.START_DATE] = _clean_string(start_date)

    if 'end_date' in body or 'endDate' in body:
        end_date = body.get('end_date')
        if end_date is None and 'endDate' in body:
            end_date = body.get('endDate')
        payload[S.Tasks.END_DATE] = _clean_string(end_date)

    if 'time_start' in body or 'timeStart' in body:
        time_start = body.get('time_start')
        if time_start is None and 'timeStart' in body:
            time_start = body.get('timeStart')
        payload[S.Tasks.TIME_START] = _clean_string(time_start)

    if 'time_end' in body or 'timeEnd' in body:
        time_end = body.get('time_end')
        if time_end is None and 'timeEnd' in body:
            time_end = body.get('timeEnd')
        payload[S.Tasks.TIME_END] = _clean_string(time_end)

    for key in ('time_spent_minutes', 'timeSpentMinutes', 'duration_minutes', 'durationMinutes'):
        if key in body:
            payload[S.Tasks.TIME_SPENT_MINUTES] = _parse_int(body.get(key))
            break

    if 'assigned_to' in body or 'assignedTo' in body:
        assigned_to = body.get('assigned_to')
        if assigned_to is None and 'assignedTo' in body:
            assigned_to = body.get('assignedTo')
        payload[S.Tasks.ASSIGNED_TO] = _parse_int(assigned_to)

    if 'status' in body:
        payload[S.Tasks.STATUS] = _clean_string(body.get('status'))

    if 'task_items' in body:
        payload[S.Tasks.TASK_ITEMS] = body.get('task_items')
    elif 'taskItems' in body:
        payload[S.Tasks.TASK_ITEMS] = body.get('taskItems')

    if 'notes' in body:
        payload[S.Tasks.NOTES] = _clean_string(body.get('notes'), allow_empty=True)

    task_date_value = payload.get(S.Tasks.TASK_DATE)
    if not payload.get(S.Tasks.START_DATE) and task_date_value:
        payload[S.Tasks.START_DATE] = task_date_value
    if not payload.get(S.Tasks.END_DATE) and task_date_value:
        payload[S.Tasks.END_DATE] = task_date_value

    return payload


def _serialize_client_response(client):
    """Convert database client representation into API response structure."""
    if not client:
        return None
    return {
        'id': client['client_id'],
        'client_id': client['client_id'],
        'name': client['client_name'],
        'client_name': client['client_name'],
        'contact_name': client.get('contact_name'),
        'contact_email': client.get('contact_email'),
        'contact_phone': client.get('contact_phone'),
        'address': client.get('address'),
        'city': client.get('city'),
        'state': client.get('state'),
        'postcode': client.get('postcode'),
        'country': client.get('country'),
        'naming_convention': client.get('naming_convention'),
    }


def _read_service_template_file():
    """Read file-based service templates."""
    try:
        if not TEMPLATE_FILE_PATH.exists():
            TEMPLATE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            return []

        with open(TEMPLATE_FILE_PATH, 'r', encoding='utf-8') as handle:
            data = json.load(handle)

        templates = data.get('templates', [])
        if isinstance(templates, list):
            return templates

        logging.error("Service template file missing 'templates' array")
        return []
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as exc:
        logging.error("Invalid JSON in service template file: %s", exc)
        return []
    except Exception as exc:
        logging.exception("Unexpected error reading service template file")
        return []


def _write_service_template_file(templates):
    """Persist file-based service templates."""
    TEMPLATE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(TEMPLATE_FILE_PATH, 'w', encoding='utf-8') as handle:
            json.dump({'templates': templates}, handle, indent=2, ensure_ascii=False)
    except Exception:
        logging.exception("Failed to write service template file")
        raise


def _normalise_file_template_payload(template_payload):
    """Validate and normalise incoming template payload for file storage."""
    if not isinstance(template_payload, dict):
        raise ValueError("Template payload must be an object")

    name = (template_payload.get('name') or '').strip()
    if not name:
        raise ValueError("Template name is required")

    sector = (template_payload.get('sector') or '').strip()
    notes = template_payload.get('notes')
    if notes is None:
        notes = template_payload.get('description') or ''

    items = template_payload.get('items')
    if isinstance(items, str):
        try:
            items = json.loads(items)
        except json.JSONDecodeError as exc:
            raise ValueError("Template items must be a valid JSON array") from exc

    # Handle PowerShell ConvertTo-Json quirk where arrays come through as { "value": [...], "Count": n }
    if isinstance(items, dict) and 'value' in items and isinstance(items['value'], list):
        items = items['value']

    if items is None:
        items = []

    if not isinstance(items, list):
        raise ValueError("Template items must be a list")

    cleaned_items = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"Template item at index {index} must be an object")
        cleaned_items.append(copy.deepcopy(item))

    return {
        'name': name,
        'sector': sector,
        'notes': notes,
        'items': cleaned_items,
    }


def _compute_template_summary(items):
    """Compute summary statistics for a template's service items."""
    total_items = len(items)
    lump_sum_items = 0
    review_items = 0
    total_reviews = 0
    estimated_value = 0.0

    for item in items:
        unit_type = item.get('unit_type')
        default_units = item.get('default_units') or 0
        try:
            default_units = float(default_units)
        except (TypeError, ValueError):
            default_units = 0

        if unit_type == 'lump_sum':
            lump_sum_items += 1
            fee = item.get('lump_sum_fee') or 0
            try:
                estimated_value += float(fee)
            except (TypeError, ValueError):
                pass
        else:
            if unit_type == 'review':
                review_items += 1
                total_reviews += int(default_units)

            rate = item.get('unit_rate') or 0
            try:
                estimated_value += float(default_units) * float(rate)
            except (TypeError, ValueError):
                pass

    return {
        'total_items': total_items,
        'lump_sum_items': lump_sum_items,
        'review_items': review_items,
        'total_reviews': total_reviews,
        'estimated_value': estimated_value,
    }


def _serialize_file_template(template, index):
    """Convert a file-based service template into API representation."""
    items = copy.deepcopy(template.get('items') or [])
    summary = _compute_template_summary(items)
    validation_errors = validate_template(template)

    return {
        'key': template.get('name'),
        'index': index,
        'name': template.get('name'),
        'sector': template.get('sector'),
        'notes': template.get('notes'),
        'description': template.get('notes'),
        'items': items,
        'summary': summary,
        'is_valid': len(validation_errors) == 0,
        'validation_errors': validation_errors,
        'source': 'file',
    }


def _get_alias_usage_stats_by_project():
    """Return alias usage statistics keyed by project ID."""
    manager = ProjectAliasManager()
    try:
        stats = manager.get_alias_usage_stats()
        return {stat['project_id']: stat for stat in stats}
    except Exception as exc:
        logging.error("Error retrieving alias usage stats: %s", exc)
        return {}
    finally:
        manager.close_connection()


def _fetch_project_alias_rows():
    """Fetch raw alias rows from the database."""
    try:
        with get_db_connection("ProjectManagement") as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT pa.{S.ProjectAliases.ALIAS_NAME},
                       pa.{S.ProjectAliases.PM_PROJECT_ID},
                       p.{S.Projects.NAME},
                       p.{S.Projects.STATUS},
                       p.{S.Projects.PROJECT_MANAGER},
                       p.created_at
                FROM dbo.{S.ProjectAliases.TABLE} pa
                LEFT JOIN dbo.{S.Projects.TABLE} p
                  ON pa.{S.ProjectAliases.PM_PROJECT_ID} = p.{S.Projects.ID}
                ORDER BY p.{S.Projects.NAME}, pa.{S.ProjectAliases.ALIAS_NAME}
                """
            )
            return cursor.fetchall()
    except Exception as exc:
        logging.error("Error fetching project aliases: %s", exc)
        return []


def _serialize_alias_row(row, stats_lookup):
    """Convert alias row into API response with issue summary."""
    alias_name, project_id, project_name, project_status, project_manager, created_at = row

    if isinstance(created_at, (datetime, date)):
        created_value = created_at.isoformat()
    else:
        created_value = created_at

    stats = stats_lookup.get(project_id, {})
    return {
        'alias_name': alias_name,
        'project_id': project_id,
        'project_name': project_name,
        'project_status': project_status,
        'project_manager': project_manager,
        'project_created_at': created_value,
        'issue_summary': {
            'total_issues': stats.get('total_issues', 0),
            'open_issues': stats.get('open_issues', 0),
            'alias_count': stats.get('alias_count', 0),
            'aliases': stats.get('aliases', ''),
            'has_issues': stats.get('has_issues', False),
        },
    }


def _get_aliases_with_stats():
    """Return all aliases enriched with issue statistics."""
    stats_lookup = _get_alias_usage_stats_by_project()
    rows = _fetch_project_alias_rows()
    return [_serialize_alias_row(row, stats_lookup) for row in rows]


def _get_alias_by_name(alias_name):
    """Find a single alias by name."""
    for alias in _get_aliases_with_stats():
        if alias['alias_name'] == alias_name:
            return alias
    return None


def _alias_exists(alias_name):
    """Check if alias already exists."""
    try:
        with get_db_connection("ProjectManagement") as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT 1 FROM dbo.{S.ProjectAliases.TABLE}
                WHERE {S.ProjectAliases.ALIAS_NAME} = ?
                """,
                (alias_name,)
            )
            return cursor.fetchone() is not None
    except Exception as exc:
        logging.error("Error checking alias existence: %s", exc)
        return False


def _project_exists(project_id):
    """Check if a project exists."""
    try:
        with get_db_connection("ProjectManagement") as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT COUNT(*) FROM dbo.{S.Projects.TABLE}
                WHERE {S.Projects.ID} = ?
                """,
                (project_id,)
            )
            return cursor.fetchone()[0] > 0
    except Exception as exc:
        logging.error("Error checking project existence: %s", exc)
        return False


# --- ServiceTemplates API ---
@app.route('/api/service_templates', methods=['GET'])
def api_get_service_templates():
    templates = get_service_templates()
    return jsonify(templates)

@app.route('/api/service_templates', methods=['POST'])
def api_create_service_template():
    body = request.get_json() or {}
    template_name = (body.get('template_name') or body.get('name') or '').strip()
    service_type = (body.get('service_type') or body.get('type') or '').strip()
    parameters = body.get('parameters')
    if parameters is None and 'items' in body:
        parameters = body['items']
    created_by = body.get('created_by') or body.get('createdBy') or body.get('created_by_id')

    if not template_name:
        return jsonify({'error': 'Template name is required'}), 400
    if not service_type:
        service_type = 'custom'
    if parameters is None:
        return jsonify({'error': 'Template parameters are required'}), 400
    if not created_by:
        created_by = 'system'
    success = create_service_template(
        template_name,
        body.get('description', ''),
        service_type,
        parameters,
        created_by
    )
    if success:
        return jsonify({'success': True}), 201
    return jsonify({'success': False}), 500

@app.route('/api/service_templates/<int:template_id>', methods=['PATCH'])
def api_update_service_template(template_id):
    body = request.get_json() or {}
    success = update_service_template(
        template_id,
        template_name=body.get('template_name'),
        description=body.get('description'),
        service_type=body.get('service_type'),
        parameters=body.get('parameters'),
        is_active=body.get('is_active')
    )
    if success:
        return jsonify({'success': True})
    return jsonify({'success': False}), 500

@app.route('/api/service_templates/<int:template_id>', methods=['DELETE'])
def api_delete_service_template(template_id):
    success = delete_service_template(template_id)
    if success:
        return jsonify({'success': True})
    return jsonify({'success': False}), 500


# --- File-based Service Templates API ---
@app.route('/api/service_templates/file', methods=['GET'])
def api_get_file_service_templates():
    templates = _read_service_template_file()
    response = [_serialize_file_template(template, index) for index, template in enumerate(templates)]
    return jsonify(response)


@app.route('/api/service_templates/file', methods=['POST'])
def api_save_file_service_template():
    body = request.get_json() or {}
    payload = body.get('template') or {}
    overwrite = bool(body.get('overwrite'))
    original_name = body.get('original_name')

    try:
        template = _normalise_file_template_payload(payload)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    validation_errors = validate_template(template)
    if validation_errors and not body.get('force'):
        return jsonify({'error': 'Template validation failed', 'details': validation_errors}), 400

    templates = _read_service_template_file()

    original_index = None
    if original_name:
        original_index = next((idx for idx, tpl in enumerate(templates) if tpl.get('name') == original_name), None)
        if original_index is None:
            return jsonify({'error': f"Template '{original_name}' not found"}), 404
        templates.pop(original_index)

    existing_index = next((idx for idx, tpl in enumerate(templates) if tpl.get('name') == template['name']), None)
    created = original_name is None and existing_index is None

    if existing_index is not None:
        if not overwrite:
            return jsonify({'error': f"Template '{template['name']}' already exists"}), 409
        templates.pop(existing_index)
        insert_index = existing_index
    else:
        insert_index = original_index if original_index is not None else len(templates)

    templates.insert(insert_index, template)

    try:
        _write_service_template_file(templates)
    except Exception:
        return jsonify({'error': 'Failed to save template file'}), 500

    response = _serialize_file_template(templates[insert_index], insert_index)
    return jsonify(response), 201 if created else 200


@app.route('/api/service_templates/file', methods=['DELETE'])
def api_delete_file_service_template():
    body = request.get_json(silent=True) or {}
    template_name = (body.get('name') or request.args.get('name') or '').strip()
    if not template_name:
        return jsonify({'error': 'Template name is required'}), 400

    templates = _read_service_template_file()
    delete_index = next((idx for idx, tpl in enumerate(templates) if tpl.get('name') == template_name), None)
    if delete_index is None:
        return jsonify({'error': f"Template '{template_name}' not found"}), 404

    templates.pop(delete_index)
    try:
        _write_service_template_file(templates)
    except Exception:
        return jsonify({'error': 'Failed to delete template'}), 500

    return jsonify({'deleted': template_name})


# --- Project Services API ---
@app.route('/api/projects/<int:project_id>/services', methods=['GET'])
def api_get_project_services(project_id):
    services = get_project_services(project_id)
    return jsonify(services)

@app.route('/api/projects/<int:project_id>/services/apply-template', methods=['POST'])
def api_apply_project_service_template(project_id):
    """Apply a file-based service template to a project."""
    body = request.get_json() or {}
    template_name = (body.get('template_name') or '').strip()
    if not template_name:
        return jsonify({'error': 'Template name is required'}), 400

    replace_existing = bool(body.get('replace_existing'))
    skip_duplicates = bool(body.get('skip_duplicates'))
    overrides = body.get('overrides') or {}

    try:
        with get_db_connection() as conn:
            service = ReviewManagementService(conn)
            result = service.apply_template(
                project_id=project_id,
                template_name=template_name,
                overrides=overrides if overrides else None,
                replace_existing=replace_existing,
                skip_existing_duplicates=skip_duplicates,
            )
            return jsonify(result)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        logging.exception("Failed to apply service template")
        return jsonify({
            'error': 'Failed to apply service template',
            'details': str(exc),
        }), 500

@app.route('/api/projects/<int:project_id>/services', methods=['POST'])
def api_create_project_service(project_id):
    body = request.get_json() or {}
    required = ['service_code', 'service_name']
    if not all(body.get(k) for k in required):
        return jsonify({'error': 'Missing required fields'}), 400
    
    service_id = create_project_service(
        project_id,
        body['service_code'],
        body['service_name'],
        phase=body.get('phase'),
        unit_type=body.get('unit_type'),
        unit_qty=body.get('unit_qty'),
        unit_rate=body.get('unit_rate'),
        lump_sum_fee=body.get('lump_sum_fee'),
        agreed_fee=body.get('agreed_fee'),
        bill_rule=body.get('bill_rule'),
        notes=body.get('notes')
    )
    if service_id:
        return jsonify({'service_id': service_id}), 201
    return jsonify({'error': 'Failed to create service'}), 500

@app.route('/api/projects/<int:project_id>/services/<int:service_id>', methods=['PATCH'])
def api_update_project_service(project_id, service_id):
    body = request.get_json() or {}
    success = update_project_service(service_id, **body)
    if success:
        return jsonify({'success': True})
    return jsonify({'error': 'Failed to update service'}), 500

@app.route('/api/projects/<int:project_id>/services/<int:service_id>', methods=['DELETE'])
def api_delete_project_service(project_id, service_id):
    success = delete_project_service(service_id)
    if success:
        return jsonify({'success': True})
    return jsonify({'error': 'Failed to delete service'}), 500


# --- Service Reviews API ---
@app.route('/api/projects/<int:project_id>/services/<int:service_id>/reviews', methods=['GET'])
def api_get_service_reviews(project_id, service_id):
    reviews = get_service_reviews(service_id)
    return jsonify(reviews)

@app.route('/api/projects/<int:project_id>/review-billing', methods=['GET'])
def api_get_project_review_billing(project_id):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    date_field = request.args.get('date_field', 'actual_issued_at')
    try:
        summary = get_service_review_billing(
            project_id,
            start_date=start_date,
            end_date=end_date,
            date_field=date_field
        )
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    return jsonify(summary)

@app.route('/api/projects/<int:project_id>/services/<int:service_id>/reviews', methods=['POST'])
def api_create_service_review(project_id, service_id):
    body = request.get_json() or {}
    required = ['cycle_no', 'planned_date']
    if not all(body.get(k) for k in required):
        return jsonify({'error': 'Missing required fields'}), 400
    
    review_id = create_service_review(
        service_id,
        body['cycle_no'],
        body['planned_date'],
        due_date=body.get('due_date'),
        disciplines=body.get('disciplines'),
        deliverables=body.get('deliverables'),
        status=body.get('status', 'planned'),
        weight_factor=body.get('weight_factor', 1.0),
        evidence_links=body.get('evidence_links'),
        invoice_reference=body.get('invoice_reference'),
        source_phase=body.get('source_phase'),
        billing_phase=body.get('billing_phase'),
        billing_rate=body.get('billing_rate'),
        billing_amount=body.get('billing_amount'),
        is_billed=body.get('is_billed')
    )
    if review_id:
        return jsonify({'review_id': review_id}), 201
    return jsonify({'error': 'Failed to create review'}), 500

@app.route('/api/projects/<int:project_id>/services/<int:service_id>/reviews/<int:review_id>', methods=['PATCH'])
def api_update_service_review(project_id, service_id, review_id):
    body = request.get_json() or {}
    success = update_service_review(review_id, **body)
    if success:
        return jsonify({'success': True})
    return jsonify({'error': 'Failed to update review'}), 500

@app.route('/api/projects/<int:project_id>/services/<int:service_id>/reviews/<int:review_id>', methods=['DELETE'])
def api_delete_service_review(project_id, service_id, review_id):
    success = delete_service_review(review_id)
    if success:
        return jsonify({'success': True})
    return jsonify({'error': 'Failed to delete review'}), 500


# Serve React app
@app.route('/')
def serve_react_app():
    return app.send_static_file('index.html')

# Serve React app for all non-API routes (SPA routing)
@app.route('/<path:path>')
def serve_react_routes(path):
    if path.startswith('api/'):
        return {'error': 'API endpoint not found'}, 404
    if path.startswith('src/') or path.endswith('.js') or path.endswith('.css'):
        return app.send_static_file(path)
    return app.send_static_file('index.html')


@app.route('/api/projects', methods=['GET', 'POST'])
def api_projects():
    if request.method == 'GET':
        projects = list_projects_full()
        return jsonify(projects)

    body = request.get_json() or {}
    payload = _extract_project_payload(body)
    try:
        result = create_project(payload)
    except ProjectValidationError as exc:
        return jsonify({'error': str(exc)}), 400
    except ProjectServiceError as exc:
        logging.exception("Failed to create project via service layer")
        return jsonify({'error': str(exc)}), 500

    return jsonify(result), 201


@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def api_delete_project_route(project_id):
    """Delete a project and all related data."""
    if not get_project_details(project_id):
        return jsonify({'error': 'Project not found'}), 404

    success = delete_project(project_id)
    if success:
        invalidate_projects_cache()
        return jsonify({'success': True})
    return jsonify({'error': 'Failed to delete project'}), 500


@app.route('/api/projects_full', methods=['GET'])
def api_get_projects_full():
    """Return enriched project data from the SQL view."""
    projects = get_projects_full()
    return jsonify(projects)


@app.route('/api/projects/stats', methods=['GET'])
def api_projects_stats():
    """Get project statistics for dashboard"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT {S.Projects.STATUS}, COUNT(*)
                FROM {S.Projects.TABLE}
                GROUP BY {S.Projects.STATUS}
                """
            )
            rows = cursor.fetchall()

        totals = { (row[0] or '').strip().lower(): int(row[1] or 0) for row in rows }
        stats = {
            'total': sum(totals.values()),
            'active': totals.get('active', 0),
            'completed': totals.get('completed', 0),
            'on_hold': totals.get('on hold', 0) + totals.get('on_hold', 0),
        }

        return jsonify(stats)
    except Exception as e:
        logging.exception("Failed to get project stats")
        return jsonify({'error': str(e)}), 500


@app.route('/api/users', methods=['GET'])
def api_get_users():
    users = get_users_list()
    data = [{'user_id': uid, 'name': name} for uid, name in users]
    return jsonify(data)


@app.route('/api/reference/<table>', methods=['GET'])
def api_reference_table(table):
    # Special handling for clients to include naming_convention
    if table == 'clients':
        return api_get_clients()
    
    rows = get_reference_options(table)
    return jsonify([{'id': r[0], 'name': r[1]} for r in rows])


@app.route('/api/naming-conventions', methods=['GET'])
def api_get_naming_conventions():
    """Get all available naming conventions"""
    try:
        from services.naming_convention_service import get_available_conventions, get_convention_summary
        
        conventions = get_available_conventions()
        result = []
        
        for code, institution in conventions:
            summary = get_convention_summary(code)
            if summary:
                result.append({
                    'code': code,
                    'name': institution,
                    'standard': summary.get('standard', ''),
                    'field_count': summary.get('field_count', 0)
                })
            else:
                result.append({
                    'code': code,
                    'name': institution,
                    'standard': '',
                    'field_count': 0
                })
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error fetching naming conventions: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/clients', methods=['GET'])
def api_get_clients():
    """Get all clients with detailed contact information."""
    try:
        clients = get_clients_detailed()
        response = [_serialize_client_response(client) for client in clients]
        return jsonify(response)
    except Exception as exc:
        logging.error("Error fetching clients: %s", exc)
        return jsonify({'error': str(exc)}), 500


@app.route('/api/clients', methods=['POST'])
def api_create_client_route():
    """Create a new client."""
    body = request.get_json() or {}
    try:
        client = create_client(body)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        logging.error("Error creating client: %s", exc)
        return jsonify({'error': 'Failed to create client'}), 500

    if not client:
        return jsonify({'error': 'Failed to create client'}), 500

    return jsonify(_serialize_client_response(client)), 201


@app.route('/api/clients/<int:client_id>', methods=['GET'])
def api_get_client(client_id):
    """Get a single client by ID."""
    client = get_client_by_id(client_id)
    if not client:
        return jsonify({'error': 'Client not found'}), 404
    return jsonify(_serialize_client_response(client))


@app.route('/api/clients/<int:client_id>', methods=['PUT', 'PATCH'])
def api_update_client_route(client_id):
    """Update an existing client."""
    existing = get_client_by_id(client_id)
    if not existing:
        return jsonify({'error': 'Client not found'}), 404

    body = request.get_json() or {}
    client = update_client(client_id, body)
    if client is None:
        return jsonify({'error': 'Failed to update client'}), 500
    return jsonify(_serialize_client_response(client))


@app.route('/api/clients/<int:client_id>', methods=['DELETE'])
def api_delete_client_route(client_id):
    """Delete a client record if it has no linked projects."""
    if not get_client_by_id(client_id):
        return jsonify({'error': 'Client not found'}), 404

    success, message = delete_client(client_id)
    if success:
        return jsonify({'success': True})
    if message:
        return jsonify({'error': message}), 400
    return jsonify({'error': 'Failed to delete client'}), 500


# --- Project Aliases API ---

@app.route('/api/project_aliases/summary', methods=['GET'])
def api_get_project_aliases_summary():
    """Get ultra-fast summary of aliases - just counts, no heavy processing"""
    try:
        from services.optimized_alias_service import OptimizedProjectAliasManager
        manager = OptimizedProjectAliasManager()
        try:
            summary = manager.get_summary_quick()
            return jsonify(summary)
        finally:
            manager.close_connection()
    except Exception as exc:
        logging.error("Error fetching alias summary: %s", exc)
        return jsonify({'error': str(exc)}), 500


@app.route('/api/project_aliases/analyze', methods=['POST'])
def api_analyze_project_aliases():
    """
    Run enhanced matching analysis on unmapped projects.
    This executes the test script logic as a service.
    
    Returns:
    {
        "summary": { confidence breakdown },
        "recommendations": [ top high-confidence matches ],
        "unmapped_details": [ all unmapped with suggestions ]
    }
    """
    try:
        from services.optimized_alias_service import run_matching_analysis
        results = run_matching_analysis()
        return jsonify(results)
    except Exception as exc:
        logging.error("Error analyzing project aliases: %s", exc)
        return jsonify({'error': str(exc)}), 500


@app.route('/api/project_aliases', methods=['GET'])
def api_get_project_aliases():
    """List all project aliases with linked issue statistics."""
    try:
        aliases = _get_aliases_with_stats()
        return jsonify(aliases)
    except Exception as exc:
        logging.error("Error fetching project aliases: %s", exc)
        return jsonify({'error': str(exc)}), 500


@app.route('/api/project_aliases', methods=['POST'])
def api_create_project_alias():
    """Create a new project alias."""
    data = request.get_json() or {}
    alias_name = (data.get('alias_name') or '').strip()
    project_id_raw = data.get('project_id')

    if not alias_name or project_id_raw is None:
        return jsonify({'error': 'alias_name and project_id are required'}), 400

    try:
        project_id = int(project_id_raw)
    except (TypeError, ValueError):
        return jsonify({'error': 'project_id must be an integer'}), 400

    if _alias_exists(alias_name):
        return jsonify({'error': 'Alias already exists'}), 409

    if not _project_exists(project_id):
        return jsonify({'error': 'Project not found'}), 404

    manager = ProjectAliasManager()
    try:
        success = manager.add_alias(project_id, alias_name)
    finally:
        manager.close_connection()

    if not success:
        return jsonify({'error': 'Failed to create alias'}), 500

    alias = _get_alias_by_name(alias_name)
    return jsonify(alias), 201


@app.route('/api/project_aliases/<path:alias_name>', methods=['PUT', 'PATCH'])
def api_update_project_alias(alias_name):
    """Update an existing alias (rename and/or reassign project)."""
    current_alias = _get_alias_by_name(alias_name)
    if not current_alias:
        return jsonify({'error': 'Alias not found'}), 404

    data = request.get_json() or {}
    new_alias_name = (data.get('alias_name') or data.get('new_alias_name') or alias_name).strip()
    project_id_raw = data.get('project_id')

    if new_alias_name != alias_name and _alias_exists(new_alias_name):
        return jsonify({'error': 'Alias name already in use'}), 409

    if project_id_raw is None:
        new_project_id = current_alias['project_id']
    else:
        try:
            new_project_id = int(project_id_raw)
        except (TypeError, ValueError):
            return jsonify({'error': 'project_id must be an integer'}), 400

        if not _project_exists(new_project_id):
            return jsonify({'error': 'Project not found'}), 404

    manager = ProjectAliasManager()
    try:
        success = manager.update_alias(alias_name, new_alias_name, new_project_id)
    finally:
        manager.close_connection()

    if not success:
        return jsonify({'error': 'Failed to update alias'}), 500

    alias = _get_alias_by_name(new_alias_name)
    return jsonify(alias)


@app.route('/api/project_aliases/<path:alias_name>', methods=['DELETE'])
def api_delete_project_alias(alias_name):
    """Delete a project alias."""
    alias = _get_alias_by_name(alias_name)
    if not alias:
        return jsonify({'error': 'Alias not found'}), 404

    manager = ProjectAliasManager()
    try:
        success = manager.delete_alias(alias_name)
    finally:
        manager.close_connection()

    if not success:
        return jsonify({'error': 'Failed to delete alias'}), 500

    return jsonify({'success': True})


@app.route('/api/project_aliases/stats', methods=['GET'])
def api_get_project_alias_stats():
    """Return per-project alias usage statistics."""
    manager = ProjectAliasManager()
    try:
        stats = manager.get_alias_usage_stats()
        return jsonify(stats)
    except Exception as exc:
        logging.error("Error fetching alias usage stats: %s", exc)
        return jsonify({'error': str(exc)}), 500
    finally:
        manager.close_connection()


@app.route('/api/project_aliases/unmapped', methods=['GET'])
def api_get_unmapped_alias_projects():
    """Return list of unmapped external project names (optimized version)."""
    try:
        from services.optimized_alias_service import OptimizedProjectAliasManager
        manager = OptimizedProjectAliasManager()
        try:
            unmapped = manager.discover_unmapped_optimized()
            return jsonify(unmapped)
        finally:
            manager.close_connection()
    except Exception as exc:
        logging.error("Error discovering unmapped projects: %s", exc)
        # Fallback to original method if optimized fails
        try:
            manager = ProjectAliasManager()
            try:
                unmapped = manager.discover_unmapped_projects()
                return jsonify(unmapped)
            finally:
                manager.close_connection()
        except:
            return jsonify({'error': str(exc)}), 500

@app.route('/api/project_aliases/validation', methods=['GET'])
def api_validate_project_aliases():
    """Run validation on project aliases and report issues."""
    manager = ProjectAliasManager()
    try:
        validation = manager.validate_aliases()
        return jsonify(validation)
    except Exception as exc:
        logging.error("Error validating project aliases: %s", exc)
        return jsonify({'error': str(exc)}), 500
    finally:
        manager.close_connection()


@app.route('/api/project_aliases/auto-map', methods=['POST'])
def api_auto_map_aliases():
    """
    Automatically create aliases for high-confidence matches.
    
    Request body:
    {
        "min_confidence": 0.85,  // Minimum confidence threshold (0.0-1.0)
        "dry_run": true          // If true, preview without creating
    }
    
    Response:
    {
        "created": [...],         // Successfully created aliases
        "skipped": [...],         // Skipped (low confidence or errors)
        "errors": [...],          // Errors during processing
        "summary": {...}          // Overall statistics
    }
    """
    body = request.get_json() or {}
    min_confidence = body.get('min_confidence', 0.85)
    dry_run = body.get('dry_run', True)
    
    # Validate confidence threshold
    try:
        min_confidence = float(min_confidence)
        if not 0.0 <= min_confidence <= 1.0:
            return jsonify({'error': 'min_confidence must be between 0.0 and 1.0'}), 400
    except (TypeError, ValueError):
        return jsonify({'error': 'min_confidence must be a number'}), 400
    
    manager = ProjectAliasManager()
    try:
        unmapped = manager.discover_unmapped_projects()
        results = {
            'created': [],
            'skipped': [],
            'errors': [],
            'summary': {
                'total_unmapped': len(unmapped),
                'eligible_for_mapping': 0,
                'successfully_mapped': 0,
                'failed': 0,
                'dry_run': dry_run
            }
        }
        
        conn = manager._get_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        for item in unmapped:
            suggestion = item.get('suggested_match')
            
            # Skip if no suggestion or confidence too low
            if not suggestion:
                results['skipped'].append({
                    'alias_name': item['project_name'],
                    'reason': 'No suggested match found',
                    'total_issues': item.get('total_issues', 0)
                })
                continue
            
            if suggestion['confidence'] < min_confidence:
                results['skipped'].append({
                    'alias_name': item['project_name'],
                    'reason': f'Confidence {suggestion["confidence"]:.1%} below threshold {min_confidence:.1%}',
                    'suggested_project': suggestion['project_name'],
                    'confidence': suggestion['confidence'],
                    'match_type': suggestion['match_type']
                })
                continue
            
            results['summary']['eligible_for_mapping'] += 1
            
            # Get project_id for the suggested match
            try:
                cursor.execute(
                    f"SELECT {S.Projects.ID} FROM {S.Projects.TABLE} WHERE {S.Projects.NAME} = ?",
                    (suggestion['project_name'],)
                )
                row = cursor.fetchone()
                
                if not row:
                    results['errors'].append({
                        'alias_name': item['project_name'],
                        'error': f"Project '{suggestion['project_name']}' not found in database"
                    })
                    results['summary']['failed'] += 1
                    continue
                
                project_id = row[0]
                
                if dry_run:
                    # Preview mode - don't actually create
                    results['created'].append({
                        'alias_name': item['project_name'],
                        'project_id': project_id,
                        'project_name': suggestion['project_name'],
                        'confidence': suggestion['confidence'],
                        'match_type': suggestion['match_type'],
                        'total_issues': item.get('total_issues', 0),
                        'dry_run': True
                    })
                    results['summary']['successfully_mapped'] += 1
                else:
                    # Actually create the alias
                    success = manager.add_alias(project_id, item['project_name'])
                    
                    if success:
                        results['created'].append({
                            'alias_name': item['project_name'],
                            'project_id': project_id,
                            'project_name': suggestion['project_name'],
                            'confidence': suggestion['confidence'],
                            'match_type': suggestion['match_type'],
                            'total_issues': item.get('total_issues', 0)
                        })
                        results['summary']['successfully_mapped'] += 1
                    else:
                        results['errors'].append({
                            'alias_name': item['project_name'],
                            'error': 'Failed to create alias (may already exist)'
                        })
                        results['summary']['failed'] += 1
            
            except Exception as e:
                results['errors'].append({
                    'alias_name': item['project_name'],
                    'error': str(e)
                })
                results['summary']['failed'] += 1
        
        return jsonify(results)
    
    except Exception as exc:
        logging.error("Error in auto-mapping aliases: %s", exc)
        return jsonify({'error': str(exc)}), 500
    finally:
        manager.close_connection()


@app.route('/api/reference/project_types', methods=['GET'])
def api_get_project_types():
    """Get all project types"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT {S.ProjectTypes.TYPE_ID}, {S.ProjectTypes.TYPE_NAME} FROM {S.ProjectTypes.TABLE} ORDER BY {S.ProjectTypes.TYPE_NAME}"
            )
            types = [{'type_id': row[0], 'type_name': row[1]} for row in cursor.fetchall()]
            return jsonify(types)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reference/project_types', methods=['POST'])
def api_create_project_type():
    """Create a new project type"""
    body = request.get_json() or {}
    type_name = body.get('name', '').strip()
    
    if not type_name:
        return jsonify({'error': 'Project type name is required'}), 400
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Check if already exists
            cursor.execute(
                f"SELECT {S.ProjectTypes.TYPE_ID} FROM {S.ProjectTypes.TABLE} WHERE {S.ProjectTypes.TYPE_NAME} = ?",
                (type_name,)
            )
            if cursor.fetchone():
                return jsonify({'error': 'Project type already exists'}), 409
            
            # Insert new type
            cursor.execute(
                f"INSERT INTO {S.ProjectTypes.TABLE} ({S.ProjectTypes.TYPE_NAME}) VALUES (?)",
                (type_name,)
            )
            conn.commit()
            
            # Get the new ID
            cursor.execute(
                f"SELECT {S.ProjectTypes.TYPE_ID} FROM {S.ProjectTypes.TABLE} WHERE {S.ProjectTypes.TYPE_NAME} = ?",
                (type_name,)
            )
            new_id = cursor.fetchone()[0]
            
            return jsonify({'id': new_id, 'name': type_name}), 201
    except Exception as e:
        logging.exception("Failed to create project type")
        return jsonify({'error': str(e)}), 500


@app.route('/api/reference/project_types/<int:type_id>', methods=['PUT'])
def api_update_project_type(type_id):
    """Update a project type name"""
    body = request.get_json() or {}
    type_name = body.get('name', '').strip()
    
    if not type_name:
        return jsonify({'error': 'Project type name is required'}), 400
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE {S.ProjectTypes.TABLE} SET {S.ProjectTypes.TYPE_NAME} = ? WHERE {S.ProjectTypes.TYPE_ID} = ?",
                (type_name, type_id)
            )
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Project type not found'}), 404
            
            return jsonify({'id': type_id, 'name': type_name})
    except Exception as e:
        logging.exception("Failed to update project type")
        return jsonify({'error': str(e)}), 500


@app.route('/api/reference/project_types/<int:type_id>', methods=['DELETE'])
def api_delete_project_type(type_id):
    """Delete a project type"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if any projects use this type
            cursor.execute(
                f"SELECT COUNT(*) FROM {S.Projects.TABLE} WHERE {S.Projects.TYPE_ID} = ?",
                (type_id,)
            )
            count = cursor.fetchone()[0]
            if count > 0:
                return jsonify({'error': f'Cannot delete: {count} project(s) are using this type'}), 409
            
            cursor.execute(
                f"DELETE FROM {S.ProjectTypes.TABLE} WHERE {S.ProjectTypes.TYPE_ID} = ?",
                (type_id,)
            )
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Project type not found'}), 404
            
            return jsonify({'success': True})
    except Exception as e:
        logging.exception("Failed to delete project type")
        return jsonify({'error': str(e)}), 500


@app.route('/api/review_tasks', methods=['GET'])
def api_get_review_tasks():
    project_id = request.args.get('project_id')
    cycle_id = request.args.get('cycle_id')
    if not project_id or not cycle_id:
        return jsonify({'error': 'project_id and cycle_id required'}), 400
    tasks = get_review_tasks(project_id, cycle_id)
    data = [
        {
            'schedule_id': sid,
            'review_date': date,
            'user': user,
            'status': status,
        }
        for sid, date, user, status in tasks
    ]
    return jsonify(data)


@app.route('/api/review_task/<int:schedule_id>', methods=['PATCH'])
def api_update_review_task(schedule_id):
    body = request.get_json() or {}
    user_id = body.get('user_id')
    if user_id is None:
        return jsonify({'error': 'user_id required'}), 400
    success = update_review_task_assignee(schedule_id, user_id)
    if success:
        return jsonify({'success': True})
    return jsonify({'success': False}), 500


@app.route('/api/project/<int:project_id>', methods=['GET'])
def api_get_project_details_endpoint(project_id):
    """Get full project details by ID"""
    try:
        projects = get_projects_full()
        project = next((p for p in projects if p.get('project_id') == project_id), None)
        if project is None:
            return jsonify({'error': 'project not found'}), 404
        return jsonify(project)
    except Exception as e:
        logging.exception("Failed to get project details")
        return jsonify({'error': str(e)}), 500


@app.route('/api/project/<int:project_id>', methods=['PATCH'])
def api_update_project_details_endpoint(project_id):
    body = request.get_json() or {}
    success = update_project_details(
        project_id,
        body.get('start_date'),
        body.get('end_date'),
        body.get('status'),
        body.get('priority'),
    )
    if success:
        invalidate_projects_cache()
    return jsonify({'success': bool(success)})


@app.route('/api/project/<int:project_id>/folders', methods=['GET', 'PATCH'])
def api_project_folders(project_id):
    if request.method == 'GET':
        models, ifc = get_project_folders(project_id)
        if models is None and ifc is None:
            return jsonify({'error': 'project not found'}), 404
        return jsonify({'model_path': models or '', 'ifc_path': ifc or ''})

    body = request.get_json() or {}
    success = update_project_folders(
        project_id,
        body.get('model_path'),
        body.get('data_path'),
        body.get('ifc_path'),
    )
    if success:
        invalidate_projects_cache()
    return jsonify({'success': bool(success)})


@app.route('/api/project', methods=['POST'])
def api_create_project():
    body = request.get_json() or {}
    payload = _extract_project_payload(body)
    try:
        result = create_project(payload)
    except ProjectValidationError as exc:
        return jsonify({'error': str(exc)}), 400
    except ProjectServiceError as exc:
        logging.exception("Failed to create project via service layer")
        return jsonify({'error': str(exc)}), 500

    return jsonify(result), 201


@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def api_update_full_project(project_id):
    """Update project fields via a generic PUT."""
    data = request.get_json() or {}
    
    # Debug logging
    print(f"\n=== PROJECT UPDATE DEBUG ===")
    print(f"Project ID: {project_id}")
    print(f"Raw start_date: {repr(data.get('start_date'))}")
    print(f"Raw end_date: {repr(data.get('end_date'))}")
    
    payload = _extract_project_payload(data)
    
    print(f"Normalized start_date: {repr(payload.get('start_date'))}")
    print(f"Normalized end_date: {repr(payload.get('end_date'))}")
    print(f"=== END DEBUG ===\n")

    try:
        result = update_project(project_id, payload)
    except ProjectValidationError as exc:
        return jsonify({'error': str(exc)}), 400
    except ProjectServiceError as exc:
        logging.exception("Failed to update project via service layer")
        return jsonify({'error': str(exc)}), 500

    return jsonify(result)


@app.route('/api/extract_files', methods=['POST'])
def api_extract_files():
    body = request.get_json() or {}
    pid = body.get('project_id')
    if not pid:
        return jsonify({'error': 'project_id required'}), 400
    folder, _ = get_project_folders(pid)
    if not folder:
        return jsonify({'error': 'model folder not set'}), 400
    success = insert_files_into_tblACCDocs(pid, folder)
    return jsonify({'success': bool(success)})


@app.route('/api/review_summary', methods=['GET'])
def api_review_summary():
    project_id = request.args.get('project_id')
    cycle_id = request.args.get('cycle_id')
    if not project_id or not cycle_id:
        return jsonify({'error': 'project_id and cycle_id required'}), 400
    summary = get_review_summary(project_id, cycle_id)
    if summary is None:
        return jsonify({'error': 'not found'}), 404
    return jsonify(summary)


@app.route('/api/contractual_links', methods=['GET'])
def api_contractual_links():
    project_id = request.args.get('project_id')
    cycle_id = request.args.get('cycle_id')
    if not project_id:
        return jsonify({'error': 'project_id required'}), 400
    links = get_contractual_links(project_id, cycle_id)
    data = [
        {
            'bep_clause': b,
            'billing_event': ev,
            'amount_due': amt,
            'status': status,
        }
        for b, ev, amt, status in links
    ]
    return jsonify(data)


@app.route('/api/cycle_ids/<int:project_id>', methods=['GET'])
def api_cycle_ids(project_id):
    cycles = get_cycle_ids(project_id)
    return jsonify(cycles)


@app.route('/api/reviews/<int:project_id>', methods=['GET'])
def api_get_review_cycles_endpoint(project_id):
    cycles = get_review_cycles(project_id)
    data = [
        {
            'review_cycle_id': cid,
            'stage_id': stage,
            'start_date': s,
            'end_date': e,
            'num_reviews': n,
        }
        for cid, stage, s, e, n in cycles
    ]
    return jsonify(data)


@app.route('/api/reviews', methods=['POST'])
def api_create_review_cycle_endpoint():
    body = request.get_json() or {}
    required = ['project_id', 'stage_id', 'start_date', 'end_date', 'num_reviews', 'created_by']
    if not all(k in body for k in required):
        return jsonify({'error': 'missing fields'}), 400
    new_id = create_review_cycle(
        body['project_id'],
        body['stage_id'],
        body['start_date'],
        body['end_date'],
        body['num_reviews'],
        body['created_by'],
    )
    if new_id is None:
        return jsonify({'success': False}), 500
    return jsonify({'id': new_id}), 201


@app.route('/api/reviews/<int:cycle_id>', methods=['PUT'])
def api_update_review_cycle_endpoint(cycle_id):
    body = request.get_json() or {}
    success = update_review_cycle(
        cycle_id,
        body.get('start_date'),
        body.get('end_date'),
        body.get('num_reviews'),
        body.get('stage_id'),
    )
    return jsonify({'success': bool(success)})


@app.route('/api/reviews/<int:cycle_id>', methods=['DELETE'])
def api_delete_review_cycle_endpoint(cycle_id):
    success = delete_review_cycle(cycle_id)
    if success:
        return jsonify({'success': True})
    return jsonify({'success': False}), 500


@app.route('/api/review_tasks/<int:schedule_id>', methods=['GET'])
def api_get_review_cycle_tasks_endpoint(schedule_id):
    tasks = get_review_cycle_tasks(schedule_id)
    data = [
        {
            'review_task_id': tid,
            'task_id': t,
            'assigned_to': a,
            'status': st,
        }
        for tid, t, a, st in tasks
    ]
    return jsonify(data)


@app.route('/api/review_tasks/<int:task_id>', methods=['PUT'])
def api_update_review_cycle_task_endpoint(task_id):
    body = request.get_json() or {}
    success = update_review_cycle_task(task_id, body.get('assigned_to'), body.get('status'))
    return jsonify({'success': bool(success)})


@app.route('/api/bep/<int:project_id>', methods=['GET'])
def api_get_bep_matrix(project_id):
    rows = get_bep_matrix(project_id)
    data = [
        {
            'section_id': sid,
            'title': title,
            'responsible_user_id': uid,
            'status': status,
            'notes': notes,
        }
        for sid, title, uid, status, notes in rows
    ]
    return jsonify(data)


@app.route('/api/bep/section', methods=['POST'])
def api_upsert_bep_section():
    body = request.get_json() or {}
    required = ['project_id', 'section_id']
    if not all(k in body for k in required):
        return jsonify({'error': 'missing fields'}), 400
    success = upsert_bep_section(
        body['project_id'],
        body['section_id'],
        body.get('responsible_user_id'),
        body.get('status'),
        body.get('notes'),
    )
    return jsonify({'success': bool(success)})


@app.route('/api/bep/status', methods=['PUT'])
def api_update_bep_status_endpoint():
    body = request.get_json() or {}
    required = ['project_id', 'section_id', 'status']
    if not all(k in body for k in required):
        return jsonify({'error': 'missing fields'}), 400
    success = update_bep_status(body['project_id'], body['section_id'], body['status'])
    return jsonify({'success': bool(success)})




@app.route('/api/projects/<int:project_id>', methods=['PATCH'])
def api_update_project(project_id):
    """Update project details - enhanced for React frontend"""
    body = request.get_json() or {}
    
    # Update project details
    success = update_project_details(
        project_id,
        body.get('start_date'),
        body.get('end_date'),
        body.get('status'),
        body.get('priority'),
    )
    
    # Update folder paths if provided
    if any(key in body for key in ['folder_path', 'ifc_folder_path', 'data_export_path']):
        update_project_folders(
            project_id,
            body.get('folder_path'),
            body.get('data_export_path'),
            body.get('ifc_folder_path'),
        )
    
    if success:
        invalidate_projects_cache()
        return jsonify({'success': True})
    return jsonify({'success': False}), 500


@app.route('/api/project_details/<int:project_id>', methods=['GET'])
def api_get_project_details_enhanced(project_id):
    """Get enhanced project details for React frontend"""
    try:
        details = get_project_details(project_id)
        if details is None:
            return jsonify({'error': 'project not found'}), 404
        
        # Get folder information
        folder_info = get_project_folders(project_id)
        
        # Combine details
        enhanced_details = {
            **details,
            'folder_path': folder_info[0] if folder_info and folder_info[0] else '',
            'ifc_folder_path': folder_info[1] if folder_info and folder_info[1] else '',
        }
        
        return jsonify(enhanced_details)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard/stats', methods=['GET'])
def api_dashboard_stats():
    """Get dashboard statistics"""
    try:
        projects = get_projects_full()
        
        stats = {
            'total_projects': len(projects),
            'active_projects': len([p for p in projects if p.get('status') == 'Active']),
            'completed_projects': len([p for p in projects if p.get('status') == 'Completed']),
            'pending_tasks': 0,  # This would require task counting logic
            'completed_tasks': 0,  # This would require task counting logic
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/project_bookmarks/<int:project_id>', methods=['GET', 'POST'])
def api_project_bookmarks_enhanced(project_id):
    """Enhanced project bookmarks API"""
    if request.method == 'GET':
        try:
            bookmarks = get_project_bookmarks(project_id)
            return jsonify(bookmarks or [])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            body = request.get_json() or {}
            success = add_bookmark(
                project_id,
                body.get('title', ''),
                body.get('url', ''),
                body.get('description', ''),
                body.get('category', 'General')
            )
            if success:
                return jsonify({'success': True}), 201
            return jsonify({'success': False}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/api/bookmark/<int:bookmark_id>', methods=['PATCH', 'DELETE'])
def api_bookmark_operations(bookmark_id):
    """Bookmark operations - update and delete"""
    if request.method == 'PATCH':
        try:
            body = request.get_json() or {}
            success = update_bookmark(
                bookmark_id,
                body.get('title'),
                body.get('url'),
                body.get('description'),
                body.get('category')
            )
            return jsonify({'success': bool(success)})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            success = delete_bookmark(bookmark_id)
            return jsonify({'success': bool(success)})
        except Exception as e:
            return jsonify({'error': str(e)}), 500


# Task Management API Endpoints

@app.route('/api/tasks/notes-view', methods=['GET'])
def api_tasks_notes_view():
    """Return tasks with the additional fields required by the Tasks & Notes view."""
    try:
        date_from = _clean_string(request.args.get('date_from')) or _clean_string(request.args.get('dateFrom'))
        date_to = _clean_string(request.args.get('date_to')) or _clean_string(request.args.get('dateTo'))
        project_id = _parse_int(request.args.get('project_id') or request.args.get('projectId'))
        user_id = _parse_int(request.args.get('user_id') or request.args.get('userId'))
        limit = request.args.get('limit', type=int)

        tasks = fetch_tasks_notes_view(
            date_from=date_from,
            date_to=date_to,
            project_id=project_id,
            user_id=user_id,
            limit=limit,
        )
        return jsonify({'tasks': tasks})
    except Exception as exc:
        logging.exception("Error fetching tasks & notes view data")
        return jsonify({'error': str(exc)}), 500


@app.route('/api/tasks', methods=['GET'])
def api_get_tasks():
    """Return task records, optionally filtered by project or user."""
    try:
        project_id = _parse_int(request.args.get('project_id') or request.args.get('projectId'))
        user_id = _parse_int(request.args.get('user_id') or request.args.get('userId') or request.args.get('assigned_to') or request.args.get('assignedTo'))
        tasks = fetch_tasks_notes_view(project_id=project_id, user_id=user_id)
        return jsonify(tasks)
    except Exception as exc:
        logging.exception("Error fetching tasks list")
        return jsonify({'error': str(exc)}), 500


@app.route('/api/tasks', methods=['POST'])
def api_create_task():
    """Create a new task entry."""
    try:
        body = request.get_json(silent=True) or {}
        payload = _extract_task_payload(body)

        task_name = payload.get(S.Tasks.TASK_NAME)
        project_id = payload.get(S.Tasks.PROJECT_ID)
        if not task_name:
            return jsonify({'error': 'task_name is required'}), 400
        if project_id is None:
            return jsonify({'error': 'project_id is required'}), 400

        created = insert_task_notes_record(payload)
        if not created:
            return jsonify({'error': 'Failed to create task'}), 500
        return jsonify(created), 201
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        logging.exception("Error creating task")
        return jsonify({'error': str(exc)}), 500


@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def api_update_task(task_id):
    """Update an existing task entry."""
    try:
        body = request.get_json(silent=True) or {}
        updates = _extract_task_payload(body)
        if not updates:
            return jsonify({'error': 'No updatable fields provided'}), 400

        updated = update_task_notes_record(task_id, updates)
        if not updated:
            return jsonify({'error': 'Task not found'}), 404
        return jsonify(updated)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        logging.exception("Error updating task")
        return jsonify({'error': str(exc)}), 500


@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def api_delete_task(task_id):
    """Delete a task by archiving or hard-deleting based on request."""
    try:
        hard_delete = _parse_bool(request.args.get('hard'))
        success = delete_task_record(task_id) if hard_delete else archive_task_record(task_id)
        if not success:
            return jsonify({'error': 'Task not found'}), 404
        return jsonify({'success': True, 'hard_deleted': hard_delete})
    except Exception as exc:
        logging.exception("Error deleting task")
        return jsonify({'error': str(exc)}), 500


@app.route('/api/tasks/<int:task_id>/items/<int:item_index>/toggle', methods=['PUT'])
def api_toggle_task_item(task_id, item_index):
    """Toggle the completion state of a specific task checklist item."""
    try:
        updated = toggle_task_item_completion(task_id, item_index)
        if not updated:
            return jsonify({'error': 'Task not found'}), 404
        return jsonify(updated)
    except IndexError:
        return jsonify({'error': 'Task item index out of range'}), 400
    except Exception as exc:
        logging.exception("Error toggling task item")
        return jsonify({'error': str(exc)}), 500


@app.route('/api/task_dependencies/<int:task_id>', methods=['GET'])
def api_get_task_dependencies(task_id):
    """Get task dependencies"""
    # Mock dependency data
    dependencies = [
        {'predecessor_id': 1, 'successor_id': task_id, 'dependency_type': 'finish_to_start'}
    ]
    return jsonify(dependencies)


@app.route('/api/resources', methods=['GET'])
def api_get_resources():
    """Get available resources/users for task assignment"""
    # This would typically come from the users table
    try:
        users = get_users_list()
        resources = [{'user_id': uid, 'name': name, 'available': True} for uid, name in users]
        return jsonify(resources)
    except Exception as e:
        # Return mock data if database not available
        mock_resources = [
            {'user_id': 1, 'name': 'John Doe', 'available': True},
            {'user_id': 2, 'name': 'Jane Smith', 'available': True},
            {'user_id': 3, 'name': 'Mike Johnson', 'available': False},
        ]
        return jsonify(mock_resources)


# ============================================================================
# DATA IMPORTS API ENDPOINTS
# ============================================================================

# --- ACC Desktop Connector File Extraction ---

@app.route('/api/projects/<int:project_id>/acc-connector-folder', methods=['GET'])
def get_project_acc_connector_folder(project_id):
    """Get configured ACC Desktop Connector folder path for project"""
    try:
        # Use model folder path (same as Tkinter app)
        folder_path, _ = get_project_folders(project_id)
        exists = os.path.exists(folder_path) if folder_path else False
        
        return jsonify({
            'project_id': project_id,
            'folder_path': folder_path,
            'exists': exists
        })
    except Exception as e:
        logging.exception(f"Error getting ACC connector folder for project {project_id}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<int:project_id>/acc-connector-folder', methods=['POST'])
def save_project_acc_connector_folder(project_id):
    """Save ACC Desktop Connector folder path for project"""
    try:
        body = request.get_json() or {}
        folder_path = body.get('folder_path')
        
        if not folder_path:
            return jsonify({'error': 'folder_path is required'}), 400
        
        # Save to model folder path (same as Tkinter app)
        success = update_project_folders(project_id, models_path=folder_path)
        
        if success:
            invalidate_projects_cache()
            return jsonify({
                'success': True,
                'project_id': project_id,
                'folder_path': folder_path
            })
        else:
            return jsonify({'error': 'Failed to save folder path'}), 500
            
    except Exception as e:
        logging.exception(f"Error saving ACC connector folder for project {project_id}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<int:project_id>/acc-connector-extract', methods=['POST'])
def extract_acc_connector_files(project_id):
    """Extract files from ACC Desktop Connector folder and insert into tblACCDocs"""
    try:
        import time
        start_time = time.time()
        
        # Use the same logic as Tkinter app: get_project_folders for model folder path
        folder_path, _ = get_project_folders(project_id)
        
        if not folder_path:
            return jsonify({'error': 'No model folder configured for this project'}), 400
        
        if not os.path.exists(folder_path):
            return jsonify({'error': f'Model folder does not exist: {folder_path}'}), 400
        
        # Extract files (this function handles DELETE and INSERT)
        success = insert_files_into_tblACCDocs(project_id, folder_path)
        
        execution_time = time.time() - start_time
        
        if success:
            # Get count of inserted files
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {S.ACCDocs.TABLE} WHERE {S.ACCDocs.PROJECT_ID} = ?", (project_id,))
                file_count = cursor.fetchone()[0]
            
            return jsonify({
                'success': True,
                'files_extracted': file_count,
                'folder_path': folder_path,
                'execution_time_seconds': round(execution_time, 2)
            })
        else:
            return jsonify({'error': 'File extraction failed'}), 500
            
    except Exception as e:
        logging.exception(f"Error extracting ACC connector files for project {project_id}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<int:project_id>/acc-connector-files', methods=['GET'])
def get_acc_connector_files(project_id):
    """Get list of files extracted from ACC Desktop Connector"""
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        file_type = request.args.get('file_type', None)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Build query with optional file type filter
            where_clause = f"{S.ACCDocs.PROJECT_ID} = ?"
            params = [project_id]
            
            if file_type:
                where_clause += f" AND {S.ACCDocs.FILE_TYPE} = ?"
                params.append(file_type)
            
            # Get total count
            cursor.execute(f"SELECT COUNT(*) FROM {S.ACCDocs.TABLE} WHERE {where_clause}", params)
            total_count = cursor.fetchone()[0]
            
            # Get paginated files
            query = f"""
                SELECT {S.ACCDocs.ID}, {S.ACCDocs.FILE_NAME}, {S.ACCDocs.FILE_PATH}, 
                       {S.ACCDocs.FILE_TYPE}, {S.ACCDocs.FILE_SIZE_KB}, 
                       {S.ACCDocs.DATE_MODIFIED}, {S.ACCDocs.CREATED_AT}
                FROM {S.ACCDocs.TABLE}
                WHERE {where_clause}
                ORDER BY {S.ACCDocs.DATE_MODIFIED} DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """
            
            cursor.execute(query, params + [offset, limit])
            rows = cursor.fetchall()
            
            files = []
            for row in rows:
                file_size_kb = float(row[4]) if row[4] else 0
                files.append({
                    'id': row[0],
                    'project_id': project_id,
                    'file_name': row[1],
                    'file_path': row[2],
                    'file_extension': row[3],  # file_type -> file_extension
                    'file_size': int(file_size_kb * 1024) if file_size_kb > 0 else None,  # Convert KB to bytes
                    'date_modified': row[5].isoformat() if row[5] else None,
                    'date_extracted': row[6].isoformat() if row[6] else None,  # created_at -> date_extracted
                    'extracted_by': None  # Add this field (not stored currently)
                })
        
        return jsonify({
            'files': files,
            'total_count': total_count,
            'page': (offset // limit) + 1,
            'page_size': limit
        })
        
    except Exception as e:
        logging.exception(f"Error getting ACC connector files for project {project_id}")
        return jsonify({'error': str(e)}), 500


# --- ACC Data Download Import (CSV/ZIP Schema Import) ---

@app.route('/api/projects/<int:project_id>/acc-data-folder', methods=['GET'])
def get_acc_data_folder(project_id):
    """Get configured ACC data export folder path"""
    try:
        # Note: ACC data folder is stored differently than connector folder
        # Using get_acc_folder_path for consistency
        folder_path = get_acc_folder_path(project_id)
        exists = os.path.exists(folder_path) if folder_path else False
        
        return jsonify({
            'project_id': project_id,
            'folder_path': folder_path,
            'exists': exists
        })
    except Exception as e:
        logging.exception(f"Error getting ACC data folder for project {project_id}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<int:project_id>/acc-data-folder', methods=['POST'])
def save_acc_data_folder(project_id):
    """Save ACC data export folder path"""
    try:
        body = request.get_json() or {}
        folder_path = body.get('folder_path')
        
        if not folder_path:
            return jsonify({'error': 'folder_path is required'}), 400
        
        success = save_acc_folder_path(project_id, folder_path)
        
        if success:
            return jsonify({
                'success': True,
                'project_id': project_id,
                'folder_path': folder_path
            })
        else:
            return jsonify({'error': 'Failed to save folder path'}), 500
            
    except Exception as e:
        logging.exception(f"Error saving ACC data folder for project {project_id}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<int:project_id>/acc-data-import', methods=['POST'])
def import_acc_data_endpoint(project_id):
    """Import ACC data from CSV/ZIP export to acc_data_schema database"""
    try:
        import time
        from handlers.acc_handler import import_acc_data
        
        start_time = time.time()
        
        body = request.get_json() or {}
        folder_path = body.get('folder_path')
        
        if not folder_path:
            # Try to get saved folder path
            folder_path = get_acc_folder_path(project_id)
        
        if not folder_path:
            return jsonify({'error': 'No ACC data folder configured'}), 400
        
        if not os.path.exists(folder_path):
            return jsonify({'error': f'ACC data folder does not exist: {folder_path}'}), 400
        
        # Compute absolute path to sql directory (relative to project root)
        # backend/app.py is one level down from project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        merge_dir = os.path.join(project_root, "sql")
        
        # Run the import (this imports to acc_data_schema database)
        # Import returns True/False or raises exception
        result = import_acc_data(folder_path, db=None, merge_dir=merge_dir, show_skip_summary=False)
        
        execution_time = time.time() - start_time
        
        # Log the import
        summary = f"Imported ACC data from {folder_path} in {execution_time:.2f}s"
        log_acc_import(project_id, os.path.basename(folder_path), summary)
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'folder_path': folder_path,
            'execution_time_seconds': round(execution_time, 2),
            'message': 'ACC data imported successfully'
        })
        
    except Exception as e:
        logging.exception(f"Error importing ACC data for project {project_id}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<int:project_id>/acc-data-import-logs', methods=['GET'])
def get_acc_data_import_logs_endpoint(project_id):
    """Get ACC data import log history for project"""
    try:
        logs = get_acc_import_logs(project_id)
        return jsonify({'logs': logs})
    except Exception as e:
        logging.exception(f"Error getting ACC import logs for project {project_id}")
        return jsonify({'error': str(e)}), 500


# --- ACC Sync (APS Auth Demo) ---

def _call_aps_service(path, method="get", params=None, json_body=None):
    """Proxy helper to the APS auth demo service."""
    base_url = APS_AUTH_SERVICE_URL.rstrip('/')
    url = f"{base_url}/{path.lstrip('/')}"
    try:
        response = requests.request(
            method,
            url,
            params=params,
            json=json_body,
            timeout=30,
        )
        try:
            payload = response.json()
        except ValueError:
            payload = {"raw": response.text or ""}
        return response.status_code, payload
    except Exception as exc:
        logging.exception("Error calling APS auth service")
        return 502, {"error": "APS auth service unavailable", "details": str(exc)}


@app.route('/api/aps-sync/login-url', methods=['GET'])
def get_aps_sync_login_url():
    """Expose the APS login URL used by the auth demo service."""
    login_path = request.args.get('path') or APS_AUTH_LOGIN_PATH or '/login-pkce'
    base_url = APS_AUTH_SERVICE_URL.rstrip('/')
    login_url = f"{base_url}/{login_path.lstrip('/')}"
    return jsonify({
        "login_url": login_url,
        "service_base": base_url,
        "flow": "pkce" if "pkce" in login_path.lower() else "3-legged",
        "note": "Opens Autodesk sign-in via aps-auth-demo service; keep this window open during login."
    })


@app.route('/api/aps-sync/hubs', methods=['GET'])
def get_aps_sync_hubs():
    """List hubs available to the currently authenticated APS user."""
    status_code, payload = _call_aps_service('my-hubs')

    # If user-token call failed, fall back to generic hubs endpoint
    if status_code >= 400 or (isinstance(payload, dict) and payload.get('error')):
        fallback_status, fallback_payload = _call_aps_service('hubs')
        if fallback_status < 400 and isinstance(fallback_payload, dict):
            payload = {**fallback_payload, "fallback_used": True}
            status_code = fallback_status
        else:
            return jsonify({
                "error": "Failed to fetch hubs from APS service",
                "details": payload,
                "upstream_status": status_code,
            }), status_code

    return jsonify(payload)


@app.route('/api/aps-sync/hubs/<path:hub_id>/projects', methods=['GET'])
def get_aps_sync_projects(hub_id):
    """List projects for a hub using APS auth demo service."""
    status_code, payload = _call_aps_service(f"my-projects/{hub_id}")

    # Fall back to app-token project listing if user token is missing
    if status_code >= 400 or (isinstance(payload, dict) and payload.get('error')):
        fallback_status, fallback_payload = _call_aps_service(f"projects/{hub_id}")
        if fallback_status < 400 and isinstance(fallback_payload, dict):
            payload = {**fallback_payload, "fallback_used": True}
            status_code = fallback_status
        else:
            return jsonify({
                "error": f"Failed to fetch projects for hub {hub_id}",
                "details": payload,
                "upstream_status": status_code,
            }), status_code

    return jsonify(payload)


# --- ACC Issues Display (Query acc_data_schema) ---

@app.route('/api/projects/<int:project_id>/acc-issues', methods=['GET'])
def get_acc_issues(project_id):
    """Get ACC issues from acc_data_schema database"""
    try:
        from config import Config

        limit = max(1, request.args.get('limit', 25, type=int) or 25)
        limit = min(limit, 200)
        page = max(1, request.args.get('page', 1, type=int) or 1)
        status = request.args.get('status')
        priority = request.args.get('priority')
        assigned_to = request.args.get('assigned_to')
        search = request.args.get('search')
        offset = (page - 1) * limit

        # Connect to acc_data_schema database
        with get_db_connection(Config.ACC_DB) as conn:
            cursor = conn.cursor()

            # Build where clause
            where_clauses = ["project_id = ?"]
            params = [project_id]

            if status:
                where_clauses.append("status = ?")
                params.append(status)

            if priority:
                where_clauses.append("priority = ?")
                params.append(priority)

            if assigned_to:
                where_clauses.append("assigned_to = ?")
                params.append(assigned_to)

            if search:
                like_value = f"%{search}%"
                where_clauses.append("(title LIKE ? OR description LIKE ?)")
                params.extend([like_value, like_value])

            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            # Get total count
            count_query = f"SELECT COUNT(*) FROM acc_data_schema.dbo.vw_issues_expanded_pm {where_sql}"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]

            # Get paginated issues
            issues_query = f"""
                SELECT issue_id,
                       title,
                       description,
                       status,
                       priority,
                       assigned_to,
                       created_at,
                       due_date,
                       owner,
                       project_name
                FROM acc_data_schema.dbo.vw_issues_expanded_pm
                {where_sql}
                ORDER BY created_at DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """

            cursor.execute(issues_query, params + [offset, limit])
            rows = cursor.fetchall()

            column_names = [col[0].lower() for col in cursor.description] if cursor.description else []

            def _serialise_date(value):
                if value is None:
                    return None
                if isinstance(value, (datetime, date)):
                    return value.isoformat()
                return str(value)

            def _to_string(value):
                if value is None:
                    return None
                return str(value)

            issues = []
            for row in rows:
                row_map = {column_names[index]: row[index] for index in range(len(column_names))}
                created_raw = row_map.get('created_at') or row_map.get('created_date')
                due_raw = row_map.get('due_date')
                issue_id = row_map.get('issue_id')
                custom_raw = row_map.get('custom_attributes')

                custom_attributes = None
                if isinstance(custom_raw, str):
                    try:
                        custom_attributes = json.loads(custom_raw)
                    except json.JSONDecodeError:
                        custom_attributes = None
                elif isinstance(custom_raw, dict):
                    custom_attributes = custom_raw

                issues.append({
                    'id': str(issue_id) if issue_id is not None else None,
                    'issue_id': str(issue_id) if issue_id is not None else None,
                    'title': _to_string(row_map.get('title')),
                    'description': _to_string(row_map.get('description')),
                    'status': _to_string(row_map.get('status')),
                    'priority': _to_string(row_map.get('priority')),
                    'type': _to_string(row_map.get('type') or row_map.get('priority')),
                    'assigned_to': _to_string(row_map.get('assigned_to')),
                    'created_date': _serialise_date(created_raw),
                    'created_at': _serialise_date(created_raw),
                    'due_date': _serialise_date(due_raw),
                    'closed_date': _serialise_date(row_map.get('closed_date')),
                    'location': _to_string(row_map.get('location')),
                    'owner': _to_string(row_map.get('owner')),
                    'project_name': _to_string(row_map.get('project_name')),
                    'custom_attributes': custom_attributes,
                })

        return jsonify({
            'issues': issues,
            'total_count': total_count,
            'page': page,
            'page_size': limit
        })

    except Exception as e:
        logging.exception(f"Error getting ACC issues for project {project_id}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<int:project_id>/acc-issues/stats', methods=['GET'])
def get_acc_issues_stats(project_id):
    """Get ACC issues statistics"""
    try:
        from config import Config

        with get_db_connection(Config.ACC_DB) as conn:
            cursor = conn.cursor()

            # Get issue counts by status
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM acc_data_schema.dbo.vw_issues_expanded_pm
                WHERE project_id = ?
                GROUP BY status
            """, (project_id,))

            status_counts = {}
            for row in cursor.fetchall():
                status_counts[row[0] or 'Unknown'] = row[1]

            # Get issue counts by priority
            cursor.execute("""
                SELECT priority, COUNT(*) as count
                FROM acc_data_schema.dbo.vw_issues_expanded_pm
                WHERE project_id = ?
                GROUP BY priority
            """, (project_id,))

            priority_counts = {}
            for row in cursor.fetchall():
                priority_counts[row[0] or 'Unknown'] = row[1]

            # Get total count
            cursor.execute(
                "SELECT COUNT(*) FROM acc_data_schema.dbo.vw_issues_expanded_pm WHERE project_id = ?",
                (project_id,)
            )
            total_count = cursor.fetchone()[0]

        return jsonify({
            'total_issues': total_count,
            'by_status': status_counts,
            'by_priority': priority_counts
        })

    except Exception as e:
        logging.exception(f"Error getting ACC issues stats for project {project_id}")
        return jsonify({'error': str(e)}), 500


# --- Combined Issues Overview ---

@app.route('/api/issues/overview', methods=['GET'])
def get_all_issues_overview():
    """Get combined issues overview for all projects"""
    try:
        overview_data = get_all_projects_issues_overview()
        return jsonify(overview_data)
    except Exception as e:
        logging.exception("Error getting all issues overview")
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<int:project_id>/issues/overview', methods=['GET'])
def get_project_issues_overview(project_id):
    """Get combined issues overview for a specific project"""
    try:
        overview_data = get_project_combined_issues_overview(project_id)
        return jsonify(overview_data)
    except Exception as e:
        logging.exception(f"Error getting issues overview for project {project_id}")
        return jsonify({'error': str(e)}), 500


# --- Revizto Issue Import ---

@app.route('/api/revizto/start-extraction', methods=['POST'])
def start_revizto_extraction():
    """Start a Revizto extraction run"""
    try:
        body = request.get_json() or {}
        export_folder = body.get('export_folder')
        notes = body.get('notes', '')

        app_path, searched_paths = _find_revizto_exporter()
        if not app_path:
            return jsonify({
                'error': 'Revizto Data Exporter not found',
                'searched_paths': searched_paths
            }), 404

        if not export_folder:
            export_folder = os.path.join(os.path.dirname(app_path), "Exports")
        os.makedirs(export_folder, exist_ok=True)

        run_id = start_revizto_extraction_run(export_folder, notes)
        if not run_id:
            return jsonify({'error': 'Failed to start extraction'}), 500

        # Kick off CLI refresh then export-all. This runs synchronously so we can record completion.
        refresh_result = _run_revizto_cli(app_path, ["refresh"])
        export_args = ["export-all"]
        if export_folder:
            export_args.append(export_folder)
        export_result = _run_revizto_cli(app_path, export_args)

        export_parsed = export_result.get("parsed") or {}
        projects_exported = 0
        try:
            if isinstance(export_parsed, dict):
                projects_exported = (
                    export_parsed.get("successfulExports")
                    or (len(export_parsed.get("results", []) or []))
                    or 0
                )
        except Exception:
            projects_exported = 0

        overall_success = (
            refresh_result.get("returncode") == 0
            and export_result.get("returncode") == 0
            and (not isinstance(export_parsed, dict) or export_parsed.get("success", True))
        )
        status_value = 'completed' if overall_success else 'failed'

        complete_revizto_extraction_run(
            run_id,
            projects_extracted=projects_exported,
            issues_extracted=0,
            licenses_extracted=0,
            status=status_value
        )

        return jsonify({
            'success': overall_success,
            'run_id': run_id,
            'status': status_value,
            'export_folder': export_folder,
            'notes': notes,
            'refresh': refresh_result,
            'export': export_result,
        })
            
    except Exception as e:
        logging.exception("Error starting Revizto extraction")
        return jsonify({'error': str(e)}), 500


@app.route('/api/revizto/status', methods=['GET'])
def get_revizto_status_cli():
    """Get Revizto exporter status via CLI."""
    try:
        app_path, searched_paths = _find_revizto_exporter()
        if not app_path:
            return jsonify({
                'error': 'Revizto Data Exporter not found',
                'searched_paths': searched_paths
            }), 404

        status_result = _run_revizto_cli(app_path, ["status"])
        if status_result.get("returncode") != 0:
            return jsonify({
                'error': 'Revizto status command failed',
                'result': status_result
            }), 500

        return jsonify({
            'success': True,
            'result': status_result
        })
    except Exception as e:
        logging.exception("Error getting Revizto status")
        return jsonify({'error': str(e)}), 500


@app.route('/api/revizto/projects', methods=['GET'])
def list_revizto_projects_cli():
    """List Revizto projects via CLI (JSON passthrough)."""
    try:
        app_path, searched_paths = _find_revizto_exporter()
        if not app_path:
            return jsonify({
                'error': 'Revizto Data Exporter not found',
                'searched_paths': searched_paths
            }), 404

        projects_result = _run_revizto_cli(app_path, ["list-projects"])
        if projects_result.get("returncode") != 0:
            return jsonify({
                'error': 'Revizto list-projects command failed',
                'result': projects_result
            }), 500

        return jsonify({
            'success': True,
            'result': projects_result
        })
    except Exception as e:
        logging.exception("Error listing Revizto projects")
        return jsonify({'error': str(e)}), 500


@app.route('/api/revizto/extraction-runs', methods=['GET'])
def get_revizto_runs():
    """Get Revizto extraction run history"""
    try:
        limit = request.args.get('limit', 50, type=int)
        runs = get_revizto_extraction_runs(limit)
        
        return jsonify({'runs': runs})
        
    except Exception as e:
        logging.exception("Error getting Revizto extraction runs")
        return jsonify({'error': str(e)}), 500


@app.route('/api/revizto/extraction-runs/last', methods=['GET'])
def get_last_revizto_run():
    """Get the most recent Revizto extraction run"""
    try:
        run = get_last_revizto_extraction_run()
        
        if run:
            return jsonify(run)
        else:
            return jsonify({'message': 'No extraction runs found'}), 404
            
    except Exception as e:
        logging.exception("Error getting last Revizto extraction run")
        return jsonify({'error': str(e)}), 500


# --- Revit Health Check Import ---

@app.route('/api/projects/<int:project_id>/health-import', methods=['POST'])
def import_revit_health_data(project_id):
    """Import Revit health check data"""
    try:
        from handlers.rvt_health_importer import import_health_data
        import time
        
        body = request.get_json() or {}
        folder_path = body.get('folder_path') or body.get('file_path')  # Support both for compatibility
        
        if not folder_path:
            return jsonify({'error': 'folder_path is required'}), 400
        
        if not os.path.exists(folder_path):
            return jsonify({'error': f'Health check folder does not exist: {folder_path}'}), 400
            
        if not os.path.isdir(folder_path):
            return jsonify({'error': f'Path must be a directory containing JSON files: {folder_path}'}), 400
        
        start_time = time.time()
        
        # Import health data (folder_path should be a folder containing JSON files)
        result = import_health_data(folder_path, project_id=project_id)
        
        execution_time = time.time() - start_time
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'folder_path': folder_path,
            'execution_time_seconds': round(execution_time, 2),
            'message': 'Health data imported successfully'
        })
        
    except Exception as e:
        logging.exception(f"Error importing Revit health data for project {project_id}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<int:project_id>/control-models', methods=['GET'])
def get_project_control_models_endpoint(project_id):
    """Return control model configuration for a project."""
    try:
        config = _build_control_model_configuration(project_id)
        return jsonify(config)
    except Exception as exc:
        logging.exception(f"Error fetching control models for project {project_id}")
        return jsonify({'error': str(exc)}), 500


@app.route('/api/projects/<int:project_id>/control-models', methods=['POST'])
def save_project_control_models(project_id):
    """Persist control model configuration for a project."""
    payload = request.get_json(silent=True) or {}
    raw_models = payload.get('control_models', [])

    if raw_models is None:
        raw_models = []
    if not isinstance(raw_models, list):
        return jsonify({'error': 'control_models must be an array'}), 400

    logging.info("Saving control models for project %s. Incoming payload: %s", project_id, raw_models)
    processed = []
    seen = set()
    zone_checks = []

    for entry in raw_models:
        if not isinstance(entry, dict):
            continue
        file_name = (entry.get('file_name') or entry.get('control_file_name') or '').strip()
        if not file_name or file_name in seen:
            continue
        seen.add(file_name)
        expected_zone = _derive_zone_code(file_name)
        provided_zone = (entry.get('zone_code') or '').strip()
        if provided_zone:
            zone_value = provided_zone.upper()
        elif expected_zone:
            zone_value = expected_zone
        else:
            zone_value = None
        processed.append({
            'file_name': file_name,
            'validation_targets': _normalise_validation_targets(entry.get('validation_targets')),
            'volume_label': (entry.get('volume_label') or '').strip() or None,
            'notes': (entry.get('notes') or '').strip() or None,
            'zone_code': zone_value,
            'is_primary': bool(entry.get('is_primary')),
        })
        zone_checks.append((file_name, zone_value, expected_zone))

    if len(processed) > 1:
        for file_name, zone_value, expected_zone in zone_checks:
            if expected_zone and not zone_value:
                return jsonify({'error': f'Zone code required for control model {file_name}.'}), 400
            if expected_zone and zone_value and zone_value.upper() != expected_zone.upper():
                return jsonify({
                    'error': f'Zone code for {file_name} must match the control file zone {expected_zone}.'
                }), 400

    primary_override = payload.get('primary_control_model')
    if primary_override:
        for model in processed:
            model['is_primary'] = model['file_name'] == primary_override

    logging.info(
        "Prepared %s control model(s) for project %s. Primary: %s. Payload: %s",
        len(processed),
        project_id,
        primary_override,
        processed,
    )

    if not set_control_models(project_id, processed):
        logging.error("Failed to persist control models for project %s", project_id)
        return jsonify({'error': 'Failed to save control model configuration'}), 500

    config = _build_control_model_configuration(project_id)
    config['message'] = 'Control model configuration updated successfully.'
    return jsonify(config)


@app.route('/api/projects/<int:project_id>/health-files', methods=['GET'])
def get_project_health_files_endpoint(project_id):
    """Get list of health check files for project"""
    try:
        # Use the proper database function to get health files
        files = get_project_health_files(project_id)
        return jsonify({'files': files})
    except Exception as e:
        logging.exception(f"Error getting health files for project {project_id}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<int:project_id>/health-summary', methods=['GET'])
def get_health_summary(project_id):
    """Get health check summary statistics"""
    try:
        from config import Config
        with get_db_connection(Config.REVIT_HEALTH_DB) as conn:
            cursor = conn.cursor()
            # Get all records first (project association may need to be handled differently)
            cursor.execute("""
                SELECT MAX(nExportedOn) as latest_check_date,
                       COUNT(*) as total_checks,
                       SUM(CAST(nWarningsCount as INT)) as total_warnings,
                       SUM(CAST(nCriticalWarningsCount as INT)) as total_errors,
                       AVG(CASE 
                               WHEN TRY_CAST(nWarningsCount as INT) IS NOT NULL THEN 
                                   CAST(100 - CASE WHEN TRY_CAST(nWarningsCount as INT) > 100 THEN 100 ELSE TRY_CAST(nWarningsCount as INT) END AS FLOAT)
                               ELSE NULL 
                          END) as avg_health_score
                FROM tblRvtProjHealth
            """)
            row = cursor.fetchone()
            
            if row:
                return jsonify({
                    'latest_check_date': row[0],
                    'total_checks': row[1] or 0,
                    'total_warnings': row[2] or 0,
                    'total_errors': row[3] or 0,
                    'avg_health_score': row[4] or 0
                })
            else:
                return jsonify({
                    'latest_check_date': None,
                    'total_checks': 0,
                    'avg_health_score': 0,
                    'total_warnings': 0,
                    'total_errors': 0
                })
    except Exception as e:
        logging.exception(f"Error getting health summary for project {project_id}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# END DATA IMPORTS API ENDPOINTS
# ============================================================================


# --- ACC Service Proxy Endpoints ---
@app.route('/api/acc/<path:path>', methods=['GET', 'POST', 'PATCH', 'PUT', 'DELETE'])
def proxy_acc_service(path):
    """Proxy requests to ACC Node.js service."""
    method = request.method
    url = f"{ACC_SERVICE_URL}/{path}"
    headers = {"Authorization": f"Bearer {ACC_SERVICE_TOKEN}", "Content-Type": "application/json"}
    try:
        resp = requests.request(
            method,
            url,
            headers=headers,
            params=request.args,
            json=request.get_json(silent=True)
        )
        return (resp.content, resp.status_code, resp.headers.items())
    except Exception as e:
        logging.exception("ACC proxy error")
        return jsonify({"error": "ACC service unavailable", "details": str(e)}), 502

# --- Revizto Service Proxy Endpoints ---
@app.route('/api/revizto/<path:path>', methods=['GET', 'POST', 'PATCH', 'PUT', 'DELETE'])
def proxy_revizto_service(path):
    """Proxy requests to Revizto .NET service."""
    method = request.method
    url = f"{REVIZTO_SERVICE_URL}/{path}"
    headers = {"Authorization": f"Bearer {REVIZTO_SERVICE_TOKEN}", "Content-Type": "application/json"}
    try:
        resp = requests.request(
            method,
            url,
            headers=headers,
            params=request.args,
            json=request.get_json(silent=True)
        )
        return (resp.content, resp.status_code, resp.headers.items())
    except Exception as e:
        logging.exception("Revizto proxy error")
        return jsonify({"error": "Revizto service unavailable", "details": str(e)}), 502


# --- File/Folder Browser Endpoints ---

@app.route('/api/file-browser/select-file', methods=['POST'])
def select_file():
    """Open file dialog and return selected file path"""
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        body = request.get_json() or {}
        title = body.get('title', 'Select File')
        file_types = body.get('file_types', [('All Files', '*.*')])
        initial_dir = body.get('initial_dir', os.path.expanduser('~'))
        
        # Create hidden root window
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title=title,
            initialdir=initial_dir,
            filetypes=file_types
        )
        
        root.destroy()
        
        if file_path:
            return jsonify({
                'success': True,
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'exists': os.path.exists(file_path)
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No file selected'
            }), 400
            
    except Exception as e:
        logging.exception("Error opening file dialog")
        return jsonify({'error': str(e)}), 500


@app.route('/api/file-browser/select-folder', methods=['POST'])
def select_folder():
    """Open folder dialog and return selected folder path"""
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        body = request.get_json() or {}
        title = body.get('title', 'Select Folder')
        initial_dir = body.get('initial_dir', os.path.expanduser('~'))
        
        # Create hidden root window
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        # Open folder dialog
        folder_path = filedialog.askdirectory(
            title=title,
            initialdir=initial_dir
        )
        
        root.destroy()
        
        if folder_path:
            return jsonify({
                'success': True,
                'folder_path': folder_path,
                'folder_name': os.path.basename(folder_path),
                'exists': os.path.exists(folder_path)
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No folder selected'
            }), 400
            
    except Exception as e:
        logging.exception("Error opening folder dialog")
        return jsonify({'error': str(e)}), 500


@app.route('/api/applications/launch', methods=['POST'])
def launch_application():
    """Launch an external application with optional arguments"""
    try:
        import subprocess
        
        body = request.get_json() or {}
        app_path = body.get('app_path')
        args = body.get('args', [])
        working_dir = body.get('working_dir')
        
        if not app_path:
            return jsonify({'error': 'app_path is required'}), 400
        
        if not os.path.exists(app_path):
            return jsonify({'error': f'Application not found: {app_path}'}), 404
        
        # Build command
        command = [app_path] + args
        
        # Launch application in background
        if os.name == 'nt':  # Windows
            subprocess.Popen(
                command,
                cwd=working_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.DETACHED_PROCESS,
                shell=False
            )
        else:  # Unix-like
            subprocess.Popen(
                command,
                cwd=working_dir,
                start_new_session=True
            )
        
        return jsonify({
            'success': True,
            'app_path': app_path,
            'args': args,
            'message': 'Application launched successfully'
        })
        
    except Exception as e:
        logging.exception("Error launching application")
        return jsonify({'error': str(e)}), 500


@app.route('/api/applications/revizto-exporter', methods=['POST'])
def launch_revizto_exporter():
    """Launch Revizto Data Exporter application"""
    try:
        # Check for custom path in request
        body = request.get_json() or {}
        custom_path = body.get('app_path')

        app_path, searched_paths = _find_revizto_exporter()
        if custom_path:
            if os.path.exists(custom_path):
                app_path = custom_path
            else:
                searched_paths.insert(0, custom_path)

        if not app_path:
            return jsonify({
                'error': 'Revizto Data Exporter not found',
                'searched_paths': searched_paths,
                'message': 'Please install Revizto Data Exporter or provide the path in the request'
            }), 404
        
        # Launch application (same method as Tkinter)
        import subprocess
        subprocess.Popen([app_path])
        
        return jsonify({
            'success': True,
            'app_path': app_path,
            'message': 'Revizto Data Exporter launched successfully'
        })
        
    except Exception as e:
        logging.exception("Error launching Revizto Data Exporter")
        return jsonify({'error': str(e)}), 500


@app.route('/api/scripts/run-health-importer', methods=['POST'])
def run_health_importer():
    """Run Revit health check importer on a folder"""
    try:
        from handlers.rvt_health_importer import import_health_data
        import time
        
        body = request.get_json() or {}
        folder_path = body.get('folder_path')
        project_id = body.get('project_id')
        
        if not folder_path:
            return jsonify({'error': 'folder_path is required'}), 400
        
        if not os.path.exists(folder_path):
            return jsonify({'error': f'Folder does not exist: {folder_path}'}), 400
        
        if not os.path.isdir(folder_path):
            return jsonify({'error': f'Path is not a folder: {folder_path}'}), 400
        
        start_time = time.time()
        
        # Import health data from folder
        result = import_health_data(folder_path, project_id=project_id, db_name=None)
        
        execution_time = time.time() - start_time
        
        return jsonify({
            'success': True,
            'folder_path': folder_path,
            'project_id': project_id,
            'execution_time_seconds': round(execution_time, 2),
            'message': 'Health data import completed successfully'
        })
        
    except Exception as e:
        logging.exception("Error running health importer")
        return jsonify({'error': str(e)}), 500


# ===================== Service Items API =====================

@app.route('/api/projects/<int:project_id>/services/<int:service_id>/items', methods=['GET'])
def api_get_service_items(project_id, service_id):
    """Get service items for a specific service."""
    try:
        from database import get_service_items
        item_type = request.args.get('type')
        items = get_service_items(service_id, item_type)
        return jsonify(items)
    except Exception as e:
        logging.exception("Error fetching service items")
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<int:project_id>/services/<int:service_id>/items', methods=['POST'])
def api_create_service_item(project_id, service_id):
    """Create a new service item."""
    try:
        from database import create_service_item
        data = request.get_json() or {}
        
        required = ['item_type', 'title', 'planned_date']
        if not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        item_id = create_service_item(
            service_id=service_id,
            item_type=data['item_type'],
            title=data['title'],
            planned_date=data['planned_date'],
            description=data.get('description'),
            due_date=data.get('due_date'),
            actual_date=data.get('actual_date'),
            status=data.get('status', 'planned'),
            priority=data.get('priority', 'medium'),
            assigned_to=data.get('assigned_to'),
            invoice_reference=data.get('invoice_reference'),
            evidence_links=data.get('evidence_links'),
            notes=data.get('notes'),
            is_billed=data.get('is_billed')
        )
        
        if item_id:
            return jsonify({'item_id': item_id, 'message': 'Service item created successfully'}), 201
        else:
            return jsonify({'error': 'Failed to create service item'}), 500
            
    except Exception as e:
        logging.exception("Error creating service item")
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<int:project_id>/services/<int:service_id>/items/<int:item_id>', methods=['PATCH'])
def api_update_service_item(project_id, service_id, item_id):
    """Update a service item."""
    try:
        from database import update_service_item
        data = request.get_json() or {}
        
        success = update_service_item(item_id, **data)
        
        if success:
            return jsonify({'message': 'Service item updated successfully'})
        else:
            return jsonify({'error': 'Service item not found or no changes made'}), 404
            
    except Exception as e:
        logging.exception("Error updating service item")
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<int:project_id>/services/<int:service_id>/items/<int:item_id>', methods=['DELETE'])
def api_delete_service_item(project_id, service_id, item_id):
    """Delete a service item."""
    try:
        from database import delete_service_item
        
        success = delete_service_item(item_id)
        
        if success:
            return jsonify({'message': 'Service item deleted successfully'})
        else:
            return jsonify({'error': 'Service item not found'}), 404
            
    except Exception as e:
        logging.exception("Error deleting service item")
        return jsonify({'error': str(e)}), 500


@app.route('/api/service_items_statistics', methods=['GET'])
def api_get_service_items_statistics():
    """Get statistics for all service items."""
    try:
        from database import get_service_items_statistics
        service_id = request.args.get('service_id', type=int)
        stats = get_service_items_statistics(service_id)
        return jsonify(stats)
    except Exception as e:
        logging.exception("Error fetching service items statistics")
        return jsonify({'error': str(e)}), 500


@app.route('/api/project_review_statistics', methods=['GET'])
def api_get_project_review_statistics():
    """Get review statistics for all projects."""
    try:
        from database import get_project_review_statistics
        stats = get_project_review_statistics()
        return jsonify(stats)
    except Exception as e:
        logging.exception("Error fetching project review statistics")
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard/timeline', methods=['GET'])
def api_get_dashboard_timeline():
    """Get aggregated project timeline data for the dashboard."""
    try:
        from database import get_dashboard_timeline
        months = request.args.get('months', type=int)
        timeline_data = get_dashboard_timeline(months=months)
        return jsonify(timeline_data)
    except Exception as e:
        logging.exception("Error fetching dashboard timeline data")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
