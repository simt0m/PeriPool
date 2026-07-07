import logging
import os
from logging.handlers import RotatingFileHandler


def configure_logging(app):
    """Attach a rotating file handler so key app events get recorded.

    Skipped during automated tests so test runs don't write into the
    same log file used for real runs of the app.
    """
    if app.config.get('TESTING'):
        return

    project_root = os.path.dirname(app.instance_path)
    log_dir = os.path.join(project_root, 'logs')
    os.makedirs(log_dir, exist_ok=True)

    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'peripool.log'),
        maxBytes=1_000_000,
        backupCount=3
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s %(message)s'
    ))

    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.DEBUG if app.config['DEBUG'] else logging.INFO)
