import os
from flask import Flask

from .extensions import db


def create_app():
    """Application factory for the Flask app.

    Builds and returns a configured Flask instance.

    Supports passing test_config to override settings for testing.
    """

    app = Flask(__name__, instance_relative_config=True)

    # --- Configuration ---
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY','dev_secret_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'peripool.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


    # Create the instance folder if it doesn't exist
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # --- Initialise extensions ---
    db.init_app(app)

    from .routes import main
    app.register_blueprint(main)

    return app