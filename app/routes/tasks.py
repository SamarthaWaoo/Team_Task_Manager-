from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..database import db
from ..models import Task, ProjectMember, User
from datetime import datetime

tasks_bp = Blueprint('tasks', __name__)

def get_current_user():
    return User.query.get(int(get_jwt_identity()))

def check_member(project_id, user_id):
    return ProjectMember.query.filter_by(
        project_id=project_id, user_id=user_id).first()

@tasks_bp.route('/project/<int:pid>', methods=['GET'])
@jwt_required()
def get_tasks(pid):
    uid = int(get_jwt_identity())
    user = get_current_user()
    if user.role != 'admin' and not check_member(pid, uid):
        return jsonify({'error': 'Access denied'}), 403
    tasks = Task.query.filter_by(project_id=pid).all()
    return jsonify([{
        'id': t.id, 'title': t.title, 'status': t.status,
        'priority': t.priority, 'assigned_to': t.assigned_to,
        'due_date': t.due_date.isoformat() if t.due_date else None,
        'is_overdue': t.is_overdue
    } for t in tasks])

@tasks_bp.route('/project/<int:pid>', methods=['POST'])
@jwt_required()
def create_task(pid):
    uid = int(get_jwt_identity())
    user = get_current_user()
    if user.role != 'admin':
        return jsonify({'error': 'Only admin can create tasks'}), 403
    if not check_member(pid, uid):
        return jsonify({'error': 'Access denied'}), 403
    data = request.get_json()
    if not data.get('title'):
        return jsonify({'error': 'Title required'}), 400
    due = None
    if data.get('due_date'):
        due = datetime.fromisoformat(data['due_date'])
    t = Task(title=data['title'],
             description=data.get('description', ''),
             project_id=pid, created_by=uid,
             assigned_to=data.get('assigned_to'),
             due_date=due,
             priority=data.get('priority', 'medium'))
    db.session.add(t)
    db.session.commit()
    return jsonify({'id': t.id, 'title': t.title}), 201

@tasks_bp.route('/<int:tid>', methods=['PATCH'])
@jwt_required()
def update_task(tid):
    uid = int(get_jwt_identity())
    user = get_current_user()
    t = Task.query.get_or_404(tid)
    if user.role != 'admin':
        if not check_member(t.project_id, uid):
            return jsonify({'error': 'Access denied'}), 403
        if t.assigned_to != uid:
            return jsonify({'error': 'You can only update your own tasks'}), 403
        allowed = ['status']
        data = {k: v for k, v in request.get_json().items() if k in allowed}
        for field in allowed:
            if field in data:
                setattr(t, field, data[field])
    else:
        data = request.get_json()
        for field in ['title', 'description', 'status', 'priority', 'assigned_to']:
            if field in data:
                setattr(t, field, data[field])
        if 'due_date' in data and data['due_date']:
            t.due_date = datetime.fromisoformat(data['due_date'])
    db.session.commit()
    return jsonify({'message': 'Updated'})

@tasks_bp.route('/<int:tid>', methods=['DELETE'])
@jwt_required()
def delete_task(tid):
    user = get_current_user()
    if user.role != 'admin':
        return jsonify({'error': 'Only admin can delete tasks'}), 403
    t = Task.query.get_or_404(tid)
    db.session.delete(t)
    db.session.commit()
    return jsonify({'message': 'Task deleted'})

@tasks_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    uid = int(get_jwt_identity())
    user = get_current_user()

    if user.role == 'admin':
        # admin sees ALL tasks across all projects
        all_tasks = Task.query.all()
        return jsonify({
            'total': len(all_tasks),
            'todo': sum(1 for t in all_tasks if t.status == 'todo'),
            'in_progress': sum(1 for t in all_tasks if t.status == 'in_progress'),
            'done': sum(1 for t in all_tasks if t.status == 'done'),
            'overdue': sum(1 for t in all_tasks if t.is_overdue)
        })
    else:
        # member sees only their assigned tasks
        my_tasks = Task.query.filter_by(assigned_to=uid).all()
        return jsonify({
            'total': len(my_tasks),
            'todo': sum(1 for t in my_tasks if t.status == 'todo'),
            'in_progress': sum(1 for t in my_tasks if t.status == 'in_progress'),
            'done': sum(1 for t in my_tasks if t.status == 'done'),
            'overdue': sum(1 for t in my_tasks if t.is_overdue)
        })