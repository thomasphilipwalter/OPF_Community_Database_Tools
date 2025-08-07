from flask import Flask
from flask_login import LoginManager
from flask_session import Session
from app.config.settings import config
from app.utils.auth_utils import get_user_by_email
import os

def create_app(config_name='default'):
    """Application factory pattern"""
    # Get the root directory of the project
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Create Flask app with proper template and static paths
    app = Flask(__name__, 
                template_folder=os.path.join(root_dir, 'templates'),
                static_folder=os.path.join(root_dir, 'static'))
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    Session(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID (email)"""
        return get_user_by_email(user_id)
    
    # Register blueprints
    from app.routes import auth, main, api
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(api.bp)
    
    return app
