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
    get_review_cycles,
    create_review_cycle,
    update_review_cycle,
    delete_review_cycle,
    get_review_cycle_tasks,
    update_review_cycle_task,
    get_bep_matrix,
    upsert_bep_section,
    update_bep_status,
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
CORS(app)


@app.route('/api/projects', methods=['GET'])
def api_get_projects():
    projects = get_projects()
    data = [{'project_id': pid, 'project_name': name} for pid, name in projects]
    return jsonify(data)


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


@app.route('/')
def serve_index():
    """Serve the React frontend."""
    return send_from_directory(app.static_folder, 'index.html')


if __name__ == '__main__':
    app.run(debug=True)
