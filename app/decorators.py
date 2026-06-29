from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def admin_required(view_function):
    """Require the current user to be an administrator.

    Redirects unauthenticated users to the login page first.

    Returns a 403 Forbidden response when a logged-in user is not an admin.
    """
    @wraps(view_function)
    @login_required
    def wrapped_view(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)

        return view_function(*args, **kwargs)

    return wrapped_view