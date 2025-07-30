from flask import Flask, jsonify, request, send_from_directory
from pathlib import Path
from flask_cors import CORS

from database import (
    get_projects,
    get_review_tasks,
    update_review_task_assignee,
    get_users_list,
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


@app.route('/')
def serve_index():
    """Serve the React frontend."""
    return send_from_directory(app.static_folder, 'index.html')


if __name__ == '__main__':
    app.run(debug=True)
