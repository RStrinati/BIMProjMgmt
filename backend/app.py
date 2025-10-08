import logging
import os
import sys
from pathlib import Path

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

from config import ACC_SERVICE_TOKEN, ACC_SERVICE_URL, REVIZTO_SERVICE_TOKEN, REVIZTO_SERVICE_URL

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import (  # noqa: E402
    create_review_cycle,
    create_service_template,
    delete_review_cycle,
    delete_service_template,
    get_bep_matrix,
    get_contractual_links,
    get_cycle_ids,
    get_project_details,
    get_project_folders,
    get_projects_full,
    get_reference_options,
    get_review_cycle_tasks,
    get_review_cycles,
    get_review_summary,
    get_review_tasks,
    get_service_templates,
    get_users_list,
    insert_files_into_tblACCDocs,
    upsert_bep_section,
    update_bep_status,
    update_project_details,
    update_project_folders,
    update_review_cycle,
    update_review_cycle_task,
    update_review_task_assignee,
)
from shared.project_service import (  # noqa: E402
    ProjectServiceError,
    ProjectValidationError,
    create_project,
    list_projects_full,
    update_project,
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
CORS(app)


def _extract_project_payload(body):
    """Normalise incoming JSON into a payload for the project service."""

    return {
        'name': body.get('project_name') or body.get('name'),
        'client_id': body.get('client_id'),
        'project_type': body.get('project_type'),
        'area': body.get('area'),
        'mw_capacity': body.get('mw_capacity'),
        'status': body.get('status'),
        'priority': body.get('priority') or body.get('priority_label'),
        'start_date': body.get('start_date'),
        'end_date': body.get('end_date'),
        'address': body.get('address'),
        'city': body.get('city'),
        'state': body.get('state'),
        'postcode': body.get('postcode'),
        'folder_path': body.get('folder_path'),
        'ifc_folder_path': body.get('ifc_folder_path'),
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


@app.route('/api/users', methods=['GET'])
def api_get_users():
    users = get_users_list()
    data = [{'user_id': uid, 'name': name} for uid, name in users]
    return jsonify(data)


@app.route('/api/reference/<table>', methods=['GET'])
def api_reference_table(table):
    rows = get_reference_options(table)
    return jsonify([{'id': r[0], 'name': r[1]} for r in rows])


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
    details = get_project_details(project_id)
    if details is None:
        return jsonify({'error': 'project not found'}), 404
    return jsonify(details)


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
    payload = _extract_project_payload(data)
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
