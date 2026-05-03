from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from ..database import db
from ..models import User

auth_bp = Blueprint('auth', __name__)

ADMIN_EMAIL    = "admin@gmail.com"
ADMIN_PASSWORD = "admin@12345"

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409
    user = User(name=data.get('name', ''), email=data['email'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    token = create_access_token(identity=str(user.id))
    return jsonify({'token': token, 'user': {
        'id': user.id, 'name': user.name,
        'email': user.email, 'role': user.role}}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email', '')).first()
    if not user or not user.check_password(data.get('password', '')):
        return jsonify({'error': 'Invalid credentials'}), 401
    token = create_access_token(identity=str(user.id))
    return jsonify({'token': token, 'user': {
        'id': user.id, 'name': user.name,
        'email': user.email, 'role': user.role}})

