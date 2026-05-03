from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..database import db
from ..models import Project, ProjectMember, User

projects_bp = Blueprint('projects', __name__)

def get_current_user():
    return User.query.get(int(get_jwt_identity()))

@projects_bp.route('/', methods=['GET'])
@jwt_required()
def get_projects():
    uid = int(get_jwt_identity())
    user = get_current_user()
    
    # admin sees ALL projects
    if user.role == 'admin':
        projects = Project.query.all()
        return jsonify([{'id': p.id, 'name': p.name,
            'description': p.description,
            'owner_id': p.owner_id} for p in projects])
    
    # members see only their projects
    memberships = ProjectMember.query.filter_by(user_id=uid).all()
    ids = [m.project_id for m in memberships]
    owned = Project.query.filter_by(owner_id=uid).all()
    all_ids = list(set(ids + [p.id for p in owned]))
    projects = Project.query.filter(Project.id.in_(all_ids)).all()
    return jsonify([{'id': p.id, 'name': p.name,
        'description': p.description,
        'owner_id': p.owner_id} for p in projects])

@projects_bp.route('/', methods=['POST'])
@jwt_required()
def create_project():
    user = get_current_user()
    
    # only admin can create projects
    if user.role != 'admin':
        return jsonify({'error': 'Only admin can create projects'}), 403
    
    data = request.get_json()
    if not data.get('name'):
        return jsonify({'error': 'Name required'}), 400
    p = Project(name=data['name'],
                description=data.get('description', ''),
                owner_id=user.id)
    db.session.add(p)
    db.session.flush()
    db.session.add(ProjectMember(project_id=p.id,
                                  user_id=user.id, role='admin'))
    db.session.commit()
    return jsonify({'id': p.id, 'name': p.name}), 201

@projects_bp.route('/<int:pid>/members', methods=['POST'])
@jwt_required()
def add_member(pid):
    user = get_current_user()
    
    # only global admin OR project admin can add members
    if user.role != 'admin':
        mem = ProjectMember.query.filter_by(
            project_id=pid, user_id=user.id).first()
        if not mem or mem.role != 'admin':
            return jsonify({'error': 'Only admin can add members'}), 403
    
    data = request.get_json()
    target = User.query.filter_by(email=data.get('email')).first()
    if not target:
        return jsonify({'error': 'User not found'}), 404
    existing = ProjectMember.query.filter_by(
        project_id=pid, user_id=target.id).first()
    if existing:
        return jsonify({'error': 'Already a member'}), 409
    db.session.add(ProjectMember(project_id=pid,
        user_id=target.id, role=data.get('role', 'member')))
    db.session.commit()
    return jsonify({'message': 'Member added'}), 201

# admin only — delete project
@projects_bp.route('/<int:pid>', methods=['DELETE'])
@jwt_required()
def delete_project(pid):
    user = get_current_user()
    if user.role != 'admin':
        return jsonify({'error': 'Only admin can delete projects'}), 403
    p = Project.query.get_or_404(pid)
    ProjectMember.query.filter_by(project_id=pid).delete()
    db.session.delete(p)
    db.session.commit()
    return jsonify({'message': 'Project deleted'})

# get members of a project
@projects_bp.route('/<int:pid>/members-list', methods=['GET'])
@jwt_required()
def get_members(pid):
    uid = int(get_jwt_identity())
    mem = ProjectMember.query.filter_by(
        project_id=pid, user_id=uid).first()
    if not mem:
        return jsonify({'error': 'Access denied'}), 403
    members = ProjectMember.query.filter_by(project_id=pid).all()
    result = []
    for m in members:
        u = User.query.get(m.user_id)
        if u:
            result.append({'id': u.id, 'name': u.name, 'email': u.email})
    return jsonify(result)