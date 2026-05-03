from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from .database import db
import os

def create_app():
    app = Flask(__name__,
        static_folder='../static',
        static_url_path='')
    CORS(app)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///taskmanager.db'
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'dev-secret')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    JWTManager(app)

    from .routes.auth import auth_bp
    from .routes.projects import projects_bp
    from .routes.tasks import tasks_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(projects_bp, url_prefix='/api/projects')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')

    @app.route('/')
    def index():
        return app.send_static_file('index.html')

    with app.app_context():
        db.create_all()
    return app