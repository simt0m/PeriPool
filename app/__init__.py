import os
from flask import Flask

from .extensions import csrf, db, login_manager


def create_app(test_config=None):
    """Application factory for the Flask app.

    Builds and returns a configured Flask instance.

    Supports passing test_config to override settings for testing.
    """

    app = Flask(__name__, instance_relative_config=True)

    # --- Configuration ---
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY','dev_secret_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'peripool.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if test_config is not None:
        app.config.update(test_config)

    # Create the instance folder if it doesn't exist
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # --- Initialise extensions ---
    db.init_app(app)
    csrf.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'


    # Import models so Flask-Login can find the user loader
    from . import models

    from .routes import main
    app.register_blueprint(main)

    return app