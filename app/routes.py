from datetime import timedelta
from decimal import Decimal, InvalidOperation

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from .decorators import admin_required
from .extensions import db, limiter
from .models import BorrowRecord, Category, ItemModel, ItemUnit, User, get_utc_now

main = Blueprint('main', __name__)

ITEM_UNIT_ADMIN_STATUSES = ['available', 'maintenance', 'inactive']

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
@limiter.limit(lambda: current_app.config['LOGIN_RATE_LIMIT'], methods=['POST'])
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

@main.route('/admin/users')
@admin_required
def admin_users():
    """Render a read-only list of users."""
    users = User.query.order_by(User.name).all()

    return render_template(
        'admin_users.html',
        users=users
    )

@main.route('/admin/inventory')
@admin_required
def admin_inventory():
    """Render a read-only view of catalogue and item units."""
    categories = Category.query.order_by(Category.name).all()

    item_models = (
        ItemModel.query
        .order_by(ItemModel.manufacturer, ItemModel.model_name)
        .all()
    )

    item_units = (
        ItemUnit.query
        .join(ItemModel)
        .order_by(ItemModel.manufacturer, ItemModel.model_name, ItemUnit.asset_tag)
        .all()
    )

    return render_template(
        'admin_inventory.html',
        categories=categories,
        item_models=item_models,
        item_units=item_units
    )

@main.route('/admin/categories/new', methods=['GET', 'POST'])
@admin_required
def admin_create_category():
    """Create a new category."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()

        if not name:
            flash('Category name is required.', 'danger')
            return render_template('admin_category_form.html', category=None)

        existing_category = (
            Category.query
            .filter(db.func.lower(Category.name) == name.lower())
            .first()
        )

        if existing_category:
            flash('A category with that name already exists.', 'danger')
            return render_template('admin_category_form.html', category=None)

        category = Category(
            name=name,
            description=description
        )

        db.session.add(category)
        db.session.commit()

        flash('Category created successfully.', 'success')
        return redirect(url_for('main.admin_inventory'))

    return render_template('admin_category_form.html', category=None)

@main.route('/admin/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_category(category_id):
    """Edit an existing category."""
    category = Category.query.get_or_404(category_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()

        if not name:
            flash('Category name is required.', 'danger')
            return render_template('admin_category_form.html', category=category)

        existing_category = (
            Category.query
            .filter(
                db.func.lower(Category.name) == name.lower(),
                Category.id != category.id
            )
            .first()
        )

        if existing_category:
            flash('Another category already uses that name.', 'danger')
            return render_template('admin_category_form.html', category=category)

        category.name = name
        category.description = description

        db.session.commit()

        flash('Category updated successfully.', 'success')
        return redirect(url_for('main.admin_inventory'))

    return render_template('admin_category_form.html', category=category)

@main.route('/admin/item-models/new', methods=['GET', 'POST'])
@admin_required
def admin_create_item_model():
    """Create a new item model."""
    categories = Category.query.order_by(Category.name).all()

    if not categories:
        flash('Create a category before adding an item model.', 'warning')
        return redirect(url_for('main.admin_inventory'))

    if request.method == 'POST':
        category_id = request.form.get('category_id', type=int)
        manufacturer = request.form.get('manufacturer', '').strip()
        model_name = request.form.get('model_name', '').strip()
        description = request.form.get('description', '').strip()
        cost_text = request.form.get('cost', '').strip()
        image_url = request.form.get('image_url', '').strip()
        is_active = request.form.get('is_active') == 'on'

        category = db.session.get(Category, category_id)

        if category is None:
            flash('Please select a valid category.', 'danger')
            return render_template(
                'admin_item_model_form.html',
                item_model=None,
                categories=categories
            )

        if not manufacturer or not model_name:
            flash('Manufacturer and model name are required.', 'danger')
            return render_template(
                'admin_item_model_form.html',
                item_model=None,
                categories=categories
            )

        cost = None

        if cost_text:
            try:
                cost = Decimal(cost_text)
            except InvalidOperation:
                flash('Cost must be a valid number.', 'danger')
                return render_template(
                    'admin_item_model_form.html',
                    item_model=None,
                    categories=categories
                )

        existing_item_model = (
            ItemModel.query
            .filter(
                db.func.lower(ItemModel.manufacturer) == manufacturer.lower(),
                db.func.lower(ItemModel.model_name) == model_name.lower()
            )
            .first()
        )

        if existing_item_model:
            flash('That manufacturer and model name already exists.', 'danger')
            return render_template(
                'admin_item_model_form.html',
                item_model=None,
                categories=categories
            )

        item_model = ItemModel(
            category_id=category.id,
            manufacturer=manufacturer,
            model_name=model_name,
            description=description,
            cost=cost,
            image_url=image_url,
            is_active=is_active
        )

        db.session.add(item_model)
        db.session.commit()

        flash('Item model created successfully.', 'success')
        return redirect(url_for('main.admin_inventory'))

    return render_template(
        'admin_item_model_form.html',
        item_model=None,
        categories=categories
    )

@main.route('/admin/item-models/<int:item_model_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_item_model(item_model_id):
    """Edit an existing item model."""
    item_model = ItemModel.query.get_or_404(item_model_id)
    categories = Category.query.order_by(Category.name).all()

    if request.method == 'POST':
        category_id = request.form.get('category_id', type=int)
        manufacturer = request.form.get('manufacturer', '').strip()
        model_name = request.form.get('model_name', '').strip()
        description = request.form.get('description', '').strip()
        cost_text = request.form.get('cost', '').strip()
        image_url = request.form.get('image_url', '').strip()
        is_active = request.form.get('is_active') == 'on'

        category = db.session.get(Category, category_id)

        if category is None:
            flash('Please select a valid category.', 'danger')
            return render_template(
                'admin_item_model_form.html',
                item_model=item_model,
                categories=categories
            )

        if not manufacturer or not model_name:
            flash('Manufacturer and model name are required.', 'danger')
            return render_template(
                'admin_item_model_form.html',
                item_model=item_model,
                categories=categories
            )

        cost = None

        if cost_text:
            try:
                cost = Decimal(cost_text)
            except InvalidOperation:
                flash('Cost must be a valid number.', 'danger')
                return render_template(
                    'admin_item_model_form.html',
                    item_model=item_model,
                    categories=categories
                )

        existing_item_model = (
            ItemModel.query
            .filter(
                db.func.lower(ItemModel.manufacturer) == manufacturer.lower(),
                db.func.lower(ItemModel.model_name) == model_name.lower(),
                ItemModel.id != item_model.id
            )
            .first()
        )

        if existing_item_model:
            flash('Another item model already uses that manufacturer and model name.', 'danger')
            return render_template(
                'admin_item_model_form.html',
                item_model=item_model,
                categories=categories
            )

        item_model.category_id = category.id
        item_model.manufacturer = manufacturer
        item_model.model_name = model_name
        item_model.description = description
        item_model.cost = cost
        item_model.image_url = image_url
        item_model.is_active = is_active

        db.session.commit()

        flash('Item model updated successfully.', 'success')
        return redirect(url_for('main.admin_inventory'))

    return render_template(
        'admin_item_model_form.html',
        item_model=item_model,
        categories=categories
    )

@main.route('/admin/item-models/<int:item_model_id>/deactivate', methods=['POST'])
@admin_required
def admin_deactivate_item_model(item_model_id):
    """Deactivate an item model."""
    item_model = ItemModel.query.get_or_404(item_model_id)

    item_model.is_active = False

    db.session.commit()

    flash('Item model deactivated successfully.', 'success')
    return redirect(url_for('main.admin_inventory'))

@main.route('/admin/item-units/new', methods=['GET', 'POST'])
@admin_required
def admin_create_item_unit():
    """Create a new item unit."""
    item_models = (
        ItemModel.query
        .filter_by(is_active=True)
        .order_by(ItemModel.manufacturer, ItemModel.model_name)
        .all()
    )

    if not item_models:
        flash('Create an active item model before adding an item unit.', 'warning')
        return redirect(url_for('main.admin_inventory'))

    if request.method == 'POST':
        item_model_id = request.form.get('item_model_id', type=int)
        asset_tag = request.form.get('asset_tag', '').strip().upper()
        status = request.form.get('status', '').strip().lower()

        item_model = db.session.get(ItemModel, item_model_id)

        if item_model is None:
            flash('Please select a valid item model.', 'danger')
            return render_template(
                'admin_item_unit_form.html',
                item_unit=None,
                item_models=item_models,
                statuses=ITEM_UNIT_ADMIN_STATUSES
            )

        if not asset_tag:
            flash('Asset tag is required.', 'danger')
            return render_template(
                'admin_item_unit_form.html',
                item_unit=None,
                item_models=item_models,
                statuses=ITEM_UNIT_ADMIN_STATUSES
            )

        if status not in ITEM_UNIT_ADMIN_STATUSES:
            flash('Please select a valid status.', 'danger')
            return render_template(
                'admin_item_unit_form.html',
                item_unit=None,
                item_models=item_models,
                statuses=ITEM_UNIT_ADMIN_STATUSES
            )

        existing_item_unit = (
            ItemUnit.query
            .filter(db.func.lower(ItemUnit.asset_tag) == asset_tag.lower())
            .first()
        )

        if existing_item_unit:
            flash('An item unit with that asset tag already exists.', 'danger')
            return render_template(
                'admin_item_unit_form.html',
                item_unit=None,
                item_models=item_models,
                statuses=ITEM_UNIT_ADMIN_STATUSES
            )

        item_unit = ItemUnit(
            item_model_id=item_model.id,
            asset_tag=asset_tag,
            status=status
        )

        db.session.add(item_unit)
        db.session.commit()

        flash('Item unit created successfully.', 'success')
        return redirect(url_for('main.admin_inventory'))

    return render_template(
        'admin_item_unit_form.html',
        item_unit=None,
        item_models=item_models,
        statuses=ITEM_UNIT_ADMIN_STATUSES
    )

@main.route('/admin/item-units/<int:item_unit_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_item_unit(item_unit_id):
    """Edit an existing item unit."""
    item_unit = ItemUnit.query.get_or_404(item_unit_id)

    if item_unit.status == 'borrowed':
        flash('Borrowed item units must be returned before they can be edited.', 'warning')
        return redirect(url_for('main.admin_inventory'))

    item_models = (
        ItemModel.query
        .filter_by(is_active=True)
        .order_by(ItemModel.manufacturer, ItemModel.model_name)
        .all()
    )

    if request.method == 'POST':
        item_model_id = request.form.get('item_model_id', type=int)
        asset_tag = request.form.get('asset_tag', '').strip().upper()
        status = request.form.get('status', '').strip().lower()

        item_model = db.session.get(ItemModel, item_model_id)

        if item_model is None:
            flash('Please select a valid item model.', 'danger')
            return render_template(
                'admin_item_unit_form.html',
                item_unit=item_unit,
                item_models=item_models,
                statuses=ITEM_UNIT_ADMIN_STATUSES
            )

        if not asset_tag:
            flash('Asset tag is required.', 'danger')
            return render_template(
                'admin_item_unit_form.html',
                item_unit=item_unit,
                item_models=item_models,
                statuses=ITEM_UNIT_ADMIN_STATUSES
            )

        if status not in ITEM_UNIT_ADMIN_STATUSES:
            flash('Please select a valid status.', 'danger')
            return render_template(
                'admin_item_unit_form.html',
                item_unit=item_unit,
                item_models=item_models,
                statuses=ITEM_UNIT_ADMIN_STATUSES
            )

        existing_item_unit = (
            ItemUnit.query
            .filter(
                db.func.lower(ItemUnit.asset_tag) == asset_tag.lower(),
                ItemUnit.id != item_unit.id
            )
            .first()
        )

        if existing_item_unit:
            flash('Another item unit already uses that asset tag.', 'danger')
            return render_template(
                'admin_item_unit_form.html',
                item_unit=item_unit,
                item_models=item_models,
                statuses=ITEM_UNIT_ADMIN_STATUSES
            )

        item_unit.item_model_id = item_model.id
        item_unit.asset_tag = asset_tag
        item_unit.status = status

        db.session.commit()

        flash('Item unit updated successfully.', 'success')
        return redirect(url_for('main.admin_inventory'))

    return render_template(
        'admin_item_unit_form.html',
        item_unit=item_unit,
        item_models=item_models,
        statuses=ITEM_UNIT_ADMIN_STATUSES
    )

@main.route('/admin/item-units/<int:item_unit_id>/delete', methods=['POST'])
@admin_required
def admin_delete_item_unit(item_unit_id):
    """Delete an item unit if it has no borrowing history."""
    item_unit = ItemUnit.query.get_or_404(item_unit_id)

    if item_unit.borrow_records:
        flash('This item unit has borrowing history and cannot be deleted. Set it to inactive instead.', 'warning')
        return redirect(url_for('main.admin_inventory'))

    db.session.delete(item_unit)
    db.session.commit()

    flash('Item unit deleted successfully.', 'success')
    return redirect(url_for('main.admin_inventory'))

@main.route('/admin/borrow-records')
@admin_required
def admin_borrow_records():
    """Render a read-only list of borrow records."""
    borrow_records = (
        BorrowRecord.query
        .order_by(BorrowRecord.borrowed_at.desc())
        .all()
    )

    return render_template(
        'admin_borrow_records.html',
        borrow_records=borrow_records
    )