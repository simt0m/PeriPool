from decimal import Decimal, InvalidOperation

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user

from ..decorators import admin_required
from ..extensions import db
from ..models import BorrowRecord, Category, ItemModel, ItemUnit, User, get_utc_now

admin = Blueprint('admin', __name__, url_prefix='/admin')

ITEM_UNIT_ADMIN_STATUSES = ['available', 'maintenance', 'inactive']

@admin.route('')
@admin_required
def dashboard():
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

@admin.route('/users')
@admin_required
def users():
    """Render a read-only list of users."""
    all_users = User.query.order_by(User.name).all()

    return render_template(
        'admin_users.html',
        users=all_users
    )

@admin.route('/inventory')
@admin_required
def inventory():
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

@admin.route('/categories/new', methods=['GET', 'POST'])
@admin_required
def create_category():
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

        current_app.logger.info(f'{current_user.email} created category: {category.name}')

        flash('Category created successfully.', 'success')
        return redirect(url_for('admin.inventory'))

    return render_template('admin_category_form.html', category=None)

@admin.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
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

        current_app.logger.info(f'{current_user.email} updated category: {category.name}')

        flash('Category updated successfully.', 'success')
        return redirect(url_for('admin.inventory'))

    return render_template('admin_category_form.html', category=category)

@admin.route('/item-models/new', methods=['GET', 'POST'])
@admin_required
def create_item_model():
    """Create a new item model."""
    categories = Category.query.order_by(Category.name).all()

    if not categories:
        flash('Create a category before adding an item model.', 'warning')
        return redirect(url_for('admin.inventory'))

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

        current_app.logger.info(
            f'{current_user.email} created item model: {item_model.manufacturer} {item_model.model_name}'
        )

        flash('Item model created successfully.', 'success')
        return redirect(url_for('admin.inventory'))

    return render_template(
        'admin_item_model_form.html',
        item_model=None,
        categories=categories
    )

@admin.route('/item-models/<int:item_model_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_item_model(item_model_id):
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

        current_app.logger.info(
            f'{current_user.email} updated item model: {item_model.manufacturer} {item_model.model_name}'
        )

        flash('Item model updated successfully.', 'success')
        return redirect(url_for('admin.inventory'))

    return render_template(
        'admin_item_model_form.html',
        item_model=item_model,
        categories=categories
    )

@admin.route('/item-models/<int:item_model_id>/deactivate', methods=['POST'])
@admin_required
def deactivate_item_model(item_model_id):
    """Deactivate an item model."""
    item_model = ItemModel.query.get_or_404(item_model_id)

    item_model.is_active = False

    db.session.commit()

    current_app.logger.info(
        f'{current_user.email} deactivated item model: {item_model.manufacturer} {item_model.model_name}'
    )

    flash('Item model deactivated successfully.', 'success')
    return redirect(url_for('admin.inventory'))

@admin.route('/item-units/new', methods=['GET', 'POST'])
@admin_required
def create_item_unit():
    """Create a new item unit."""
    item_models = (
        ItemModel.query
        .filter_by(is_active=True)
        .order_by(ItemModel.manufacturer, ItemModel.model_name)
        .all()
    )

    if not item_models:
        flash('Create an active item model before adding an item unit.', 'warning')
        return redirect(url_for('admin.inventory'))

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

        current_app.logger.info(f'{current_user.email} created item unit: {item_unit.asset_tag}')

        flash('Item unit created successfully.', 'success')
        return redirect(url_for('admin.inventory'))

    return render_template(
        'admin_item_unit_form.html',
        item_unit=None,
        item_models=item_models,
        statuses=ITEM_UNIT_ADMIN_STATUSES
    )

@admin.route('/item-units/<int:item_unit_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_item_unit(item_unit_id):
    """Edit an existing item unit."""
    item_unit = ItemUnit.query.get_or_404(item_unit_id)

    if item_unit.status == 'borrowed':
        flash('Borrowed item units must be returned before they can be edited.', 'warning')
        return redirect(url_for('admin.inventory'))

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

        current_app.logger.info(f'{current_user.email} updated item unit: {item_unit.asset_tag}')

        flash('Item unit updated successfully.', 'success')
        return redirect(url_for('admin.inventory'))

    return render_template(
        'admin_item_unit_form.html',
        item_unit=item_unit,
        item_models=item_models,
        statuses=ITEM_UNIT_ADMIN_STATUSES
    )

@admin.route('/item-units/<int:item_unit_id>/delete', methods=['POST'])
@admin_required
def delete_item_unit(item_unit_id):
    """Delete an item unit if it has no borrowing history."""
    item_unit = ItemUnit.query.get_or_404(item_unit_id)

    if item_unit.borrow_records:
        flash('This item unit has borrowing history and cannot be deleted. Set it to inactive instead.', 'warning')
        return redirect(url_for('admin.inventory'))

    asset_tag = item_unit.asset_tag

    db.session.delete(item_unit)
    db.session.commit()

    current_app.logger.info(f'{current_user.email} deleted item unit: {asset_tag}')

    flash('Item unit deleted successfully.', 'success')
    return redirect(url_for('admin.inventory'))

@admin.route('/borrow-records')
@admin_required
def borrow_records():
    """Render a read-only list of borrow records."""
    all_borrow_records = (
        BorrowRecord.query
        .order_by(BorrowRecord.borrowed_at.desc())
        .all()
    )

    return render_template(
        'admin_borrow_records.html',
        borrow_records=all_borrow_records
    )
