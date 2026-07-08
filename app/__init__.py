import os
from flask import Flask

from .extensions import csrf, db, limiter, login_manager, talisman
from .errors import register_error_handlers
from .logging_config import configure_logging
from config import get_config


def create_app(test_config=None):
    """Application factory for the Flask app.

    Builds and returns a configured Flask instance.

    Supports passing test_config to override settings for testing.
    """

    app = Flask(__name__, instance_relative_config=True)

    # --- Configuration ---
    app.config.from_object(get_config(os.environ.get('FLASK_CONFIG')))

    app.config.setdefault(
        'SQLALCHEMY_DATABASE_URI',
        'sqlite:///' + os.path.join(app.instance_path, 'peripool.db')
    )

    if test_config is not None:
        app.config.update(test_config)

    # Create the instance folder if it doesn't exist
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    configure_logging(app)

    # --- Initialise extensions ---
    db.init_app(app)
    csrf.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    limiter.init_app(app)

    talisman.init_app(
        app,
        force_https=app.config['FORCE_HTTPS'],
        session_cookie_secure=app.config['FORCE_HTTPS'],
        content_security_policy={'default-src': "'self'"}
    )

    register_error_handlers(app)

    from .blueprints.auth import auth
    from .blueprints.catalogue import catalogue
    from .blueprints.admin import admin

    app.register_blueprint(auth)
    app.register_blueprint(catalogue)
    app.register_blueprint(admin)

    return app