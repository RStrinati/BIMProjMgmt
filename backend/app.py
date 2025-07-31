from flask import Flask, jsonify, request, send_from_directory
from pathlib import Path
from flask_cors import CORS

from database import (
    get_projects,
    get_review_tasks,
    update_review_task_assignee,
    get_users_list,
    get_project_details,
    update_project_details,
    update_project_folders,
    insert_project,
    insert_files_into_tblACCDocs,
    get_project_folders,
    get_review_summary,
    get_contractual_links,
    get_cycle_ids,
    # newly added helpers
    get_projects_full,
    update_project_financials,
    update_client_info,
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
CORS(app)


@app.route('/api/projects', methods=['GET'])
def api_get_projects():
    projects = get_projects()
    data = [{'project_id': pid, 'project_name': name} for pid, name in projects]
    return jsonify(data)


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
    name = body.get('project_name')
    if not name:
        return jsonify({'error': 'project_name required'}), 400
    success = insert_project(name, body.get('folder_path', ''), body.get('ifc_folder_path'))
    if success:
        return jsonify({'success': True}), 201
    return jsonify({'success': False}), 500


@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def api_update_full_project(project_id):
    """Update financial and client details for a project."""
    data = request.get_json() or {}

    update_project_financials(
        project_id,
        data.get('contract_value'),
        data.get('payment_terms'),
    )
    update_client_info(
        project_id,
        data.get('client_contact'),
        data.get('contact_email'),
    )

    return jsonify({'message': 'Project updated'})


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


@app.route('/')
def serve_index():
    """Serve the React frontend."""
    return send_from_directory(app.static_folder, 'index.html')


if __name__ == '__main__':
    app.run(debug=True)
