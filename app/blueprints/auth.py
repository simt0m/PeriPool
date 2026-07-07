from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import db, limiter
from ..models import User

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Register new user account."""
    if current_user.is_authenticated:
        return redirect(url_for('catalogue.dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not name or not email or not password:
            flash('Please complete all required fields.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return render_template('register.html')

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash('An account already exists for that email address.', 'danger')
            return render_template('register.html')

        user = User(
            name=name,
            email=email,
            is_admin=False,
            is_active=True
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        current_app.logger.info(f'New user registered: {user.email}')

        login_user(user)

        flash('Account created successfully!', 'success')
        return redirect(url_for('catalogue.dashboard'))

    return render_template('register.html')

@auth.route('/login', methods=['GET', 'POST'])
@limiter.limit(lambda: current_app.config['LOGIN_RATE_LIMIT'], methods=['POST'])
def login():
    """Log in an existing user."""
    if current_user.is_authenticated:
        return redirect(url_for('catalogue.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if user is None or not user.is_active or not user.check_password(password):
            current_app.logger.warning(f'Failed login attempt for: {email}')
            flash('Invalid email or password.', 'danger')
            return render_template('login.html')

        login_user(user)

        current_app.logger.info(f'User logged in: {user.email}')

        flash('You have been logged in.', 'success')
        return redirect(url_for('catalogue.dashboard'))

    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('catalogue.home'))
