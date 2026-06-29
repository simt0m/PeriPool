from datetime import timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from .decorators import admin_required
from .extensions import db
from .models import BorrowRecord, Category, ItemModel, ItemUnit, User, get_utc_now

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

@main.route('/borrow/<int:item_model_id>', methods=['POST'])
@login_required
def borrow_item(item_model_id):
    """Borrow one available unit for the selected item model."""
    item_model = ItemModel.query.filter_by(
        id=item_model_id,
        is_active=True
    ).first_or_404()

    existing_borrow = (
        BorrowRecord.query
        .join(ItemUnit)
        .filter(
            BorrowRecord.user_id == current_user.id,
            BorrowRecord.status == 'active',
            ItemUnit.item_model_id == item_model.id
        )
        .first()
    )

    if existing_borrow:
        flash('You already have this model on loan.', 'warning')
        return redirect(url_for('main.catalogue'))

    available_unit = (
        ItemUnit.query
        .filter_by(item_model_id=item_model.id, status='available')
        .order_by(ItemUnit.asset_tag)
        .first()
    )

    if available_unit is None:
        flash('No units are currently available for this model.', 'warning')
        return redirect(url_for('main.catalogue'))

    available_unit.status = 'borrowed'

    borrow_record = BorrowRecord(
        user_id=current_user.id,
        item_unit_id=available_unit.id,
        due_at=get_utc_now() + timedelta(days=7),
        status='active'
    )

    db.session.add(borrow_record)
    db.session.commit()

    flash(
        f'You have borrowed {item_model.manufacturer} {item_model.model_name}.',
        'success'
    )

    return redirect(url_for('main.dashboard'))

@main.route('/return/<int:borrow_record_id>', methods=['POST'])
@login_required
def return_item(borrow_record_id):
    """Return an active borrowed item."""
    borrow_record = BorrowRecord.query.filter_by(
        id=borrow_record_id,
        user_id=current_user.id,
        status='active'
    ).first_or_404()

    borrow_record.status = 'returned'
    borrow_record.returned_at = get_utc_now()
    borrow_record.item_unit.status = 'available'

    db.session.commit()

    flash('Item returned successfully.', 'success')
    return redirect(url_for('main.dashboard'))

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

@main.route('/admin')
@admin_required
def admin_dashboard():
    """Render the administrator dashboard."""
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()

    total_categories = Category.query.count()
    total_item_models = ItemModel.query.count()
    active_item_models = ItemModel.query.filter_by(is_active=True).count()

    total_item_units = ItemUnit.query.count()
    available_item_units = ItemUnit.query.filter_by(status='available').count()
    borrowed_item_units = ItemUnit.query.filter_by(status='borrowed').count()
    maintenance_item_units = ItemUnit.query.filter_by(status='maintenance').count()

    active_borrow_records = BorrowRecord.query.filter_by(status='active').count()

    overdue_borrow_records = (
        BorrowRecord.query
        .filter(
            BorrowRecord.status == 'active',
            BorrowRecord.returned_at.is_(None),
            BorrowRecord.due_at < get_utc_now()
        )
        .count()
    )

    return render_template(
        'admin_dashboard.html',
        total_users=total_users,
        active_users=active_users,
        total_categories=total_categories,
        total_item_models=total_item_models,
        active_item_models=active_item_models,
        total_item_units=total_item_units,
        available_item_units=available_item_units,
        borrowed_item_units=borrowed_item_units,
        maintenance_item_units=maintenance_item_units,
        active_borrow_records=active_borrow_records,
        overdue_borrow_records=overdue_borrow_records,
    )

@main.app_errorhandler(403)
def forbidden(error):
    """Render a 403 Forbidden error page."""
    return render_template('403.html'), 403