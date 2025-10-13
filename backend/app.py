import logging
import os
import sys
from pathlib import Path

# Add parent directory to path FIRST so we can import config and database
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

from config import ACC_SERVICE_TOKEN, ACC_SERVICE_URL, REVIZTO_SERVICE_TOKEN, REVIZTO_SERVICE_URL

from database import (  # noqa: E402
    add_bookmark,
    create_review_cycle,
    create_service_template,
    delete_bookmark,
    delete_review_cycle,
    delete_service_template,
    get_acc_folder_path,
    get_acc_import_logs,
    get_bep_matrix,
    get_contractual_links,
    get_cycle_ids,
    get_db_connection,
    get_last_revizto_extraction_run,
    get_project_bookmarks,
    get_project_details,
    get_project_folders,
    get_project_health_files,
    get_projects_full,
    get_reference_options,
    get_review_cycle_tasks,
    get_review_cycles,
    get_review_summary,
    get_review_tasks,
    get_revizto_extraction_runs,
    get_service_templates,
    get_users_list,
    insert_files_into_tblACCDocs,
    log_acc_import,
    save_acc_folder_path,
    start_revizto_extraction_run,
    update_bookmark,
    upsert_bep_section,
    update_bep_status,
    update_project_details,
    update_project_folders,
    update_review_cycle,
    update_review_cycle_task,
    update_review_task_assignee,
    update_service_template,
)
from shared.project_service import (  # noqa: E402
    ProjectServiceError,
    ProjectValidationError,
    create_project,
    list_projects_full,
    update_project,
)
from constants import schema as S  # noqa: E402

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
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
        'project_type': body.get('project_type'),
        'area': body.get('area'),
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
    }


# --- ServiceTemplates API ---
@app.route('/api/service_templates', methods=['GET'])
def api_get_service_templates():
    templates = get_service_templates()
    return jsonify(templates)

@app.route('/api/service_templates', methods=['POST'])
def api_create_service_template():
    body = request.get_json() or {}
    required = ['template_name', 'service_type', 'parameters', 'created_by']
    if not all(body.get(k) for k in required):
        return jsonify({'error': 'Missing required fields'}), 400
    success = create_service_template(
        body['template_name'],
        body.get('description', ''),
        body['service_type'],
        body['parameters'],
        body['created_by']
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


@app.route('/api/projects_full', methods=['GET'])
def api_get_projects_full():
    """Return enriched project data from the SQL view."""
    projects = get_projects_full()
    return jsonify(projects)


@app.route('/api/projects/stats', methods=['GET'])
def api_projects_stats():
    """Get project statistics for dashboard"""
    try:
        projects = get_projects_full()
        
        stats = {
            'total': len(projects),
            'active': len([p for p in projects if p.get('status') == 'Active']),
            'completed': len([p for p in projects if p.get('status') == 'Completed']),
            'on_hold': len([p for p in projects if p.get('status') == 'On Hold']),
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
    rows = get_reference_options(table)
    return jsonify([{'id': r[0], 'name': r[1]} for r in rows])


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

@app.route('/api/tasks', methods=['GET'])
def api_get_tasks():
    """Get tasks for a project"""
    project_id = request.args.get('project_id')
    if not project_id:
        return jsonify({'error': 'project_id required'}), 400
    
    # For now, return mock data until we implement the full task system
    mock_tasks = [
        {
            'task_id': 1,
            'task_name': 'Design Review Phase 1',
            'project_id': project_id,
            'priority': 'High',
            'status': 'In Progress',
            'progress_percentage': 75,
            'assigned_to': 'John Doe',
            'start_date': '2024-01-15',
            'end_date': '2024-01-30',
            'estimated_hours': 40,
            'description': 'Complete architectural design review'
        },
        {
            'task_id': 2,
            'task_name': 'Structural Analysis',
            'project_id': project_id,
            'priority': 'Medium',
            'status': 'Not Started',
            'progress_percentage': 0,
            'assigned_to': 'Jane Smith',
            'start_date': '2024-02-01',
            'end_date': '2024-02-15',
            'estimated_hours': 60,
            'description': 'Perform structural calculations and analysis'
        }
    ]
    
    return jsonify(mock_tasks)


@app.route('/api/tasks', methods=['POST'])
def api_create_task():
    """Create a new task"""
    body = request.get_json() or {}
    
    required_fields = ['task_name', 'project_id']
    if not all(field in body for field in required_fields):
        return jsonify({'error': 'task_name and project_id are required'}), 400
    
    # For now, return success - would integrate with EnhancedTaskManager
    task_data = {
        'task_id': 999,  # Mock ID
        'success': True,
        **body
    }
    
    return jsonify(task_data), 201


@app.route('/api/tasks/<int:task_id>', methods=['PATCH'])
def api_update_task(task_id):
    """Update a task"""
    body = request.get_json() or {}
    
    # For now, return success - would integrate with task update logic
    return jsonify({'success': True, 'task_id': task_id})


@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def api_delete_task(task_id):
    """Delete a task"""
    # For now, return success - would integrate with task deletion logic
    return jsonify({'success': True})


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
        
        # Run the import (this imports to acc_data_schema database)
        # Import returns True/False or raises exception
        result = import_acc_data(folder_path, db=None, merge_dir="sql", show_skip_summary=False)
        
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


# --- ACC Issues Display (Query acc_data_schema) ---

@app.route('/api/projects/<int:project_id>/acc-issues', methods=['GET'])
def get_acc_issues(project_id):
    """Get ACC issues from acc_data_schema database"""
    try:
        from config import Config
        
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        status = request.args.get('status', None)
        priority = request.args.get('priority', None)
        assigned_to = request.args.get('assigned_to', None)
        
        # Connect to acc_data_schema database
        with get_db_connection(Config.ACC_DB) as conn:
            cursor = conn.cursor()
            
            # Build where clause
            where_clauses = []
            params = []
            
            if status:
                where_clauses.append("status = ?")
                params.append(status)
            
            if priority:
                where_clauses.append("priority = ?")
                params.append(priority)
            
            if assigned_to:
                where_clauses.append("assigned_to = ?")
                params.append(assigned_to)
            
            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM acc_data_schema.dbo.vw_issues_expanded_pm {where_sql}"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]
            
            # Get paginated issues
            issues_query = f"""
                SELECT issue_id, title, description, status, priority, 
                       assigned_to, created_at, due_date, owner, project_name
                FROM acc_data_schema.dbo.vw_issues_expanded_pm
                {where_sql}
                ORDER BY created_at DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """
            
            cursor.execute(issues_query, params + [offset, limit])
            rows = cursor.fetchall()
            
            issues = []
            for row in rows:
                issues.append({
                    'issue_id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'status': row[3],
                    'priority': row[4],
                    'assigned_to': row[5],
                    'created_at': row[6].isoformat() if row[6] else None,
                    'due_date': row[7].isoformat() if row[7] else None,
                    'owner': row[8],
                    'project_name': row[9]
                })
        
        return jsonify({
            'issues': issues,
            'total_count': total_count,
            'page': (offset // limit) + 1,
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
                GROUP BY status
            """)
            
            status_counts = {}
            for row in cursor.fetchall():
                status_counts[row[0] or 'Unknown'] = row[1]
            
            # Get issue counts by priority
            cursor.execute("""
                SELECT priority, COUNT(*) as count
                FROM acc_data_schema.dbo.vw_issues_expanded_pm
                GROUP BY priority
            """)
            
            priority_counts = {}
            for row in cursor.fetchall():
                priority_counts[row[0] or 'Unknown'] = row[1]
            
            # Get total count
            cursor.execute("SELECT COUNT(*) FROM acc_data_schema.dbo.vw_issues_expanded_pm")
            total_count = cursor.fetchone()[0]
        
        return jsonify({
            'total_issues': total_count,
            'by_status': status_counts,
            'by_priority': priority_counts
        })
        
    except Exception as e:
        logging.exception(f"Error getting ACC issues stats for project {project_id}")
        return jsonify({'error': str(e)}), 500


# --- Revizto Issue Import ---

@app.route('/api/revizto/start-extraction', methods=['POST'])
def start_revizto_extraction():
    """Start a Revizto extraction run"""
    try:
        body = request.get_json() or {}
        export_folder = body.get('export_folder')
        notes = body.get('notes', '')
        
        run_id = start_revizto_extraction_run(export_folder, notes)
        
        if run_id:
            return jsonify({
                'success': True,
                'run_id': run_id,
                'export_folder': export_folder,
                'notes': notes
            })
        else:
            return jsonify({'error': 'Failed to start extraction'}), 500
            
    except Exception as e:
        logging.exception("Error starting Revizto extraction")
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
        file_path = body.get('file_path')
        
        if not file_path:
            return jsonify({'error': 'file_path is required'}), 400
        
        if not os.path.exists(file_path):
            return jsonify({'error': f'Health check file does not exist: {file_path}'}), 400
        
        start_time = time.time()
        
        # Import health data
        result = import_health_data(file_path, project_id)
        
        execution_time = time.time() - start_time
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'file_path': file_path,
            'execution_time_seconds': round(execution_time, 2),
            'message': 'Health data imported successfully'
        })
        
    except Exception as e:
        logging.exception(f"Error importing Revit health data for project {project_id}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<int:project_id>/health-files', methods=['GET'])
def get_project_health_files_endpoint(project_id):
    """Get list of health check files for project"""
    try:
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
            
            # Get summary statistics (adjust query based on actual schema)
            cursor.execute("""
                SELECT COUNT(*) as total_checks,
                       SUM(CASE WHEN status = 'Passed' THEN 1 ELSE 0 END) as passed,
                       SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) as failed,
                       SUM(CASE WHEN status = 'Warning' THEN 1 ELSE 0 END) as warnings
                FROM RevitHealthCheckDB.dbo.HealthChecks
                WHERE project_id = ?
            """, (project_id,))
            
            row = cursor.fetchone()
        
        if row:
            return jsonify({
                'total_checks': row[0] or 0,
                'passed': row[1] or 0,
                'failed': row[2] or 0,
                'warnings': row[3] or 0
            })
        else:
            return jsonify({
                'total_checks': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0
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
        # Common installation paths for Revizto Data Exporter
        # Get project root (one level up from backend)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        possible_paths = [
            # Local development path (same as Tkinter app)
            os.path.join(project_root, "tools", "ReviztoDataExporter.exe"),
            # Local development path alternative
            os.path.join(project_root, "services", "revizto-dotnet", "ReviztoDataExporter", "bin", "Debug", "net9.0-windows", "win-x64", "ReviztoDataExporter.exe"),
            # Standard installation paths
            r"C:\Program Files\Revizto\DataExporter\ReviztoDataExporter.exe",
            r"C:\Program Files (x86)\Revizto\DataExporter\ReviztoDataExporter.exe",
            r"C:\Revizto\DataExporter\ReviztoDataExporter.exe",
        ]
        
        # Check for custom path in request
        body = request.get_json() or {}
        custom_path = body.get('app_path')
        
        if custom_path:
            possible_paths.insert(0, custom_path)
        
        # Find the executable
        app_path = None
        for path in possible_paths:
            if os.path.exists(path):
                app_path = path
                break
        
        if not app_path:
            return jsonify({
                'error': 'Revizto Data Exporter not found',
                'searched_paths': possible_paths,
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
        result = import_health_data(folder_path, db_name=None)
        
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
