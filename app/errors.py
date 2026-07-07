from flask import current_app, render_template, request
from flask_login import current_user
from flask_wtf.csrf import CSRFError


def register_error_handlers(app):
    """Register friendly error pages for the app.

    Kept separate from the blueprint so these apply no matter which
    part of the site raised the error.
    """

    @app.errorhandler(403)
    def forbidden(error):
        who = current_user.email if current_user.is_authenticated else 'anonymous'
        current_app.logger.warning(f'Forbidden: {who} tried to access {request.path}')
        return render_template('403.html'), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404

    @app.errorhandler(429)
    def rate_limited(error):
        current_app.logger.warning(f'Rate limit exceeded for {request.remote_addr} on {request.path}')
        return render_template('rate_limited.html'), 429

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        current_app.logger.warning(f'CSRF check failed on {request.path}: {error.description}')
        return render_template('csrf_error.html', reason=error.description), 400
