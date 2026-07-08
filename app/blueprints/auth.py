from flask import Blueprint, current_app, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import db, limiter
from ..forms import LoginForm, RegisterForm
from ..models import User

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Register new user account."""
    if current_user.is_authenticated:
        return redirect(url_for('catalogue.dashboard'))

    form = RegisterForm()

    if form.validate_on_submit():
        user = User(
            name=form.name.data,
            email=form.email.data,
            is_admin=False,
            is_active=True
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        current_app.logger.info(f'New user registered: {user.email}')

        login_user(user)

        flash('Account created successfully!', 'success')
        return redirect(url_for('catalogue.dashboard'))

    return render_template('register.html', form=form)

@auth.route('/login', methods=['GET', 'POST'])
@limiter.limit(lambda: current_app.config['LOGIN_RATE_LIMIT'], methods=['POST'])
def login():
    """Log in an existing user."""
    if current_user.is_authenticated:
        return redirect(url_for('catalogue.dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user is None or not user.is_active or not user.check_password(form.password.data):
            current_app.logger.warning(f'Failed login attempt for: {form.email.data}')
            flash('Invalid email or password.', 'danger')
            return render_template('login.html', form=form)

        login_user(user)

        current_app.logger.info(f'User logged in: {user.email}')

        flash('You have been logged in.', 'success')
        return redirect(url_for('catalogue.dashboard'))

    return render_template('login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('catalogue.home'))
