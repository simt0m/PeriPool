from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from .extensions import db
from .models import BorrowRecord, ItemModel, User

main = Blueprint('main', __name__)

@main.route('/')
def home():
    """Render the home page."""
    return render_template('index.html')

@main.route('/catalogue')
def catalogue():
    """Render the item model catalogue."""
    item_models = (
        ItemModel.query
        .filter_by(is_active=True)
        .order_by(ItemModel.manufacturer, ItemModel.model_name)
        .all()
    )

    return render_template('catalogue.html', item_models=item_models)

@main.route('/register', methods=['GET', 'POST'])
def register():
    """Register new user account."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
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

        login_user(user)

        flash('Account created successfully!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('register.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    """Log in an existing user."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if user is None or not user.is_active or not user.check_password(password):
            flash('Invalid email or password.', 'danger')
            return render_template('login.html')
        
        login_user(user)

        flash('You have been logged in.', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))

@main.route('/dashboard')
@login_required
def dashboard():
    """Render the user dashboard."""
    active_borrow_records = (
        BorrowRecord.query
        .filter_by(user_id=current_user.id, status='active')
        .order_by(BorrowRecord.due_at)
        .all()
    )

    previous_borrow_records = (
        BorrowRecord.query
        .filter(
            BorrowRecord.user_id == current_user.id,
            BorrowRecord.status != 'active'
        )
        .order_by(BorrowRecord.borrowed_at.desc())
        .all()
    )

    return render_template(
        'dashboard.html',
        active_borrow_records=active_borrow_records,
        previous_borrow_records=previous_borrow_records
    )